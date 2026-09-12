package com.oneday.app

import android.Manifest
import android.annotation.SuppressLint
import android.content.Intent
import android.content.pm.PackageManager
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.provider.Settings
import android.speech.RecognitionListener
import android.speech.RecognizerIntent
import android.speech.SpeechRecognizer
import android.view.View
import android.webkit.JavascriptInterface
import android.webkit.WebChromeClient
import android.webkit.WebResourceRequest
import android.webkit.WebSettings
import android.webkit.WebView
import android.webkit.WebViewClient
import android.widget.Toast
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AppCompatActivity
import androidx.core.content.ContextCompat
import org.json.JSONObject
import java.util.Locale

/**
 * OneDay 一日 — Android WebView 壳
 *
 * - 加载本地 assets/index.html（纯前端模式，IndexedDB 持久化，无需后端）
 * - 原生语音桥 AndroidBridge：用系统 SpeechRecognizer 做连续语音识别，
 *   把累积文本推给 JS（window.OnDayNative.onSpeechResult），
 *   JS 侧在 AndroidBridge 存在时自动走 startAndroidVoice/stopAndroidVoice。
 */
class MainActivity : AppCompatActivity() {

    private lateinit var webView: WebView
    private var speechRecognizer: SpeechRecognizer? = null
    private var keepListening = false
    private var bridgeReady = false
    private var lastResultTime = 0L

    private val recordAudioPermission =
        registerForActivityResult(ActivityResultContracts.RequestPermission()) { granted ->
            if (granted) {
                startNativeListening()
            } else {
                pushJs("window.OnDayNative && window.OnDayNative.onSpeechError('permission denied')")
            }
        }

    @SuppressLint("SetJavaScriptEnabled")
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        webView = WebView(this)
        setContentView(webView)

        configureWebView()
        registerBridge()
        webView.loadUrl("file:///android_asset/index.html")
    }

    @SuppressLint("SetJavaScriptEnabled")
    private fun configureWebView() {
        val ws = webView.settings
        ws.javaScriptEnabled = true
        ws.domStorageEnabled = true
        ws.databaseEnabled = true
        ws.allowFileAccess = true
        ws.allowContentAccess = true
        ws.setSupportMultipleWindows(false)
        ws.mediaPlaybackRequiresUserGesture = false
        ws.cacheMode = WebSettings.LOAD_DEFAULT
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.LOLLIPOP) {
            ws.mixedContentMode = WebSettings.MIXED_CONTENT_ALWAYS_ALLOW
        }
        // 中文界面
        ws.textZoom = 100

        webView.webChromeClient = WebChromeClient()
        webView.webViewClient = object : WebViewClient() {
            override fun shouldOverrideUrlLoading(view: WebView?, request: WebResourceRequest?): Boolean {
                val url = request?.url?.toString() ?: return false
                // 站外链接交给系统浏览器
                if (!url.startsWith("file://")) {
                    try {
                        startActivity(Intent(Intent.ACTION_VIEW, Uri.parse(url)))
                    } catch (e: Exception) {
                        Toast.makeText(this@MainActivity, "无法打开链接", Toast.LENGTH_SHORT).show()
                    }
                    return true
                }
                return false
            }
        }

        // 沉浸式（隐藏状态栏/导航栏，可滑动唤出）
        window.decorView.systemUiVisibility =
            (View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY
                    or View.SYSTEM_UI_FLAG_FULLSCREEN
                    or View.SYSTEM_UI_FLAG_HIDE_NAVIGATION
                    or View.SYSTEM_UI_FLAG_LAYOUT_STABLE)
    }

    private fun registerBridge() {
        webView.addJavascriptInterface(AndroidBridge(), "AndroidBridge")
    }

    // ===== JS 注入工具 =====
    private fun pushJs(code: String) {
        runOnUiThread {
            try {
                webView.evaluateJavascript(code, null)
            } catch (e: Exception) {
                // 页面未就绪时忽略
            }
        }
    }

    private fun jsString(s: String): String = JSONObject.quote(s)

    // ===== 原生语音桥 =====
    inner class AndroidBridge {
        @JavascriptInterface
        fun startListening(): Boolean {
            if (!SpeechRecognizer.isRecognitionAvailable(this@MainActivity)) {
                pushJs("window.OnDayNative && window.OnDayNative.onSpeechError('recognizer unavailable')")
                return false
            }
            if (ContextCompat.checkSelfPermission(
                    this@MainActivity,
                    Manifest.permission.RECORD_AUDIO
                ) != PackageManager.PERMISSION_GRANTED
            ) {
                recordAudioPermission.launch(Manifest.permission.RECORD_AUDIO)
                return true // 授权回调里再真正启动
            }
            startNativeListening()
            return true
        }

        @JavascriptInterface
        fun stopListening() {
            keepListening = false
            try {
                speechRecognizer?.stopListening()
                speechRecognizer?.cancel()
                speechRecognizer?.destroy()
            } catch (e: Exception) {
                // ignore
            }
            speechRecognizer = null
        }
    }

    private fun startNativeListening() {
        keepListening = true
        lastResultTime = System.currentTimeMillis()
        try {
            speechRecognizer?.destroy()
        } catch (e: Exception) { /* ignore */ }

        val sr = SpeechRecognizer.createSpeechRecognizer(this)
        speechRecognizer = sr
        sr.setRecognitionListener(object : RecognitionListener {
            override fun onReadyForSpeech(params: Bundle?) {
                bridgeReady = true
            }

            override fun onBeginningOfSpeech() { /* 保持 */ }

            override fun onRmsChanged(rmsdB: Float) { /* 可用于波形，暂不接 */ }

            override fun onBufferReceived(buffer: ByteArray?) { /* 保持 */ }

            override fun onEndOfSpeech() {
                // 一段说完；若仍保持录音，等待 onResults 后再重启
            }

            override fun onError(error: Int) {
                val msg = when (error) {
                    SpeechRecognizer.ERROR_NO_MATCH -> "no match"
                    SpeechRecognizer.ERROR_SPEECH_TIMEOUT -> "no speech"
                    SpeechRecognizer.ERROR_NETWORK -> "network"
                    SpeechRecognizer.ERROR_INSUFFICIENT_PERMISSIONS -> "permission"
                    SpeechRecognizer.ERROR_RECOGNIZER_BUSY -> "busy"
                    else -> "error $error"
                }
                if (keepListening) {
                    // 无语音/超时属正常停顿，静默重启以保持连续
                    restartListening()
                } else {
                    pushJs("window.OnDayNative && window.OnDayNative.onSpeechError('${jsString(msg)}')")
                }
            }

            override fun onResults(results: Bundle?) {
                val text = results
                    ?.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION)
                    ?.firstOrNull() ?: ""
                lastResultTime = System.currentTimeMillis()
                if (text.isNotBlank()) {
                    pushJs("window.OnDayNative && window.OnDayNative.onSpeechResult(${jsString(text)})")
                }
                if (keepListening) restartListening()
            }

            override fun onPartialResults(partialResults: Bundle?) { /* final 为准 */ }

            override fun onEvent(eventType: Int, params: Bundle?) { /* 保持 */ }
        })

        val intent = Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH).apply {
            putExtra(
                RecognizerIntent.EXTRA_LANGUAGE_MODEL,
                RecognizerIntent.LANGUAGE_MODEL_FREE_FORM
            )
            putExtra(RecognizerIntent.EXTRA_LANGUAGE, Locale.SIMPLIFIED_CHINESE.toLanguageTag())
            putExtra(RecognizerIntent.EXTRA_PARTIAL_RESULTS, true)
            putExtra(RecognizerIntent.EXTRA_MAX_RESULTS, 1)
        }
        try {
            sr.startListening(intent)
        } catch (e: Exception) {
            keepListening = false
            pushJs("window.OnDayNative && window.OnDayNative.onSpeechError('${jsString(e.message ?: "start failed")}')")
        }
    }

    private fun restartListening() {
        try {
            speechRecognizer?.cancel()
            speechRecognizer?.startListening(
                Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH).apply {
                    putExtra(
                        RecognizerIntent.EXTRA_LANGUAGE_MODEL,
                        RecognizerIntent.LANGUAGE_MODEL_FREE_FORM
                    )
                    putExtra(
                        RecognizerIntent.EXTRA_LANGUAGE,
                        Locale.SIMPLIFIED_CHINESE.toLanguageTag()
                    )
                    putExtra(RecognizerIntent.EXTRA_PARTIAL_RESULTS, true)
                    putExtra(RecognizerIntent.EXTRA_MAX_RESULTS, 1)
                }
            )
        } catch (e: Exception) {
            if (keepListening) pushJs("window.OnDayNative && window.OnDayNative.onSpeechError('restart failed')")
        }
    }

    override fun onDestroy() {
        keepListening = false
        try {
            speechRecognizer?.cancel()
            speechRecognizer?.destroy()
        } catch (e: Exception) { /* ignore */ }
        speechRecognizer = null
        super.onDestroy()
    }
}
