package example.app.platform

import android.content.Context
import android.os.Build
import android.os.VibrationEffect
import android.os.Vibrator
import android.os.VibratorManager
import example.app.settings.AppSettings

// The target manifest must declare android.permission.VIBRATE.
// VibrationEffect requires API 26. Adapt this module for an older minimum SDK.
class AndroidHaptics(context: Context) {
    private val vibrator: Vibrator? = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
        (context.getSystemService(Context.VIBRATOR_MANAGER_SERVICE) as? VibratorManager)?.defaultVibrator
    } else {
        @Suppress("DEPRECATION")
        context.getSystemService(Context.VIBRATOR_SERVICE) as? Vibrator
    }

    val isSupported: Boolean get() = vibrator?.hasVibrator() == true

    fun feedback(settings: AppSettings) = preview(settings.vibrationMs)

    fun preview(durationMs: Int) {
        val device = vibrator ?: return
        if (!device.hasVibrator() || durationMs <= 0) return
        device.vibrate(VibrationEffect.createOneShot(durationMs.coerceIn(1, 200).toLong(), VibrationEffect.DEFAULT_AMPLITUDE))
    }
}
