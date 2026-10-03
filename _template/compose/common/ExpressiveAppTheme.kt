package example.app.ui

import androidx.compose.material3.ColorScheme
import androidx.compose.material3.ExperimentalMaterial3ExpressiveApi
import androidx.compose.material3.MaterialExpressiveTheme
import androidx.compose.material3.MotionScheme
import androidx.compose.runtime.Composable
import androidx.compose.runtime.remember
import androidx.compose.ui.graphics.Color
import com.materialkolor.PaletteStyle
import com.materialkolor.dynamicColorScheme
import example.app.settings.AppSettings
import example.app.settings.ColorSource

@OptIn(ExperimentalMaterial3ExpressiveApi::class)
@Composable
fun ExpressiveAppTheme(
    settings: AppSettings,
    systemDark: Boolean,
    wallpaperScheme: ColorScheme? = null,
    content: @Composable () -> Unit,
) {
    val dark = settings.isDark(systemDark)
    val seed = if (settings.colorSource == ColorSource.CUSTOM) settings.seedArgb else 0xFF6750A4
    val generatedScheme = remember(seed, dark) {
        dynamicColorScheme(
            seedColor = Color(seed.toInt()),
            isDark = dark,
            isAmoled = false,
            style = PaletteStyle.TonalSpot,
            contrastLevel = 0.0,
        )
    }
    val scheme = if (settings.colorSource == ColorSource.WALLPAPER) {
        wallpaperScheme ?: generatedScheme
    } else {
        generatedScheme
    }
    // Keep one theme call so settings changes preserve the content's state.
    MaterialExpressiveTheme(
        colorScheme = scheme,
        motionScheme = MotionScheme.expressive(),
        content = content,
    )
}
