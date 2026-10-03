package example.app.platform

import androidx.compose.runtime.Composable
import androidx.compose.runtime.State
import androidx.compose.runtime.produceState
import kotlinx.coroutines.delay
import kotlinx.coroutines.isActive
import org.jetbrains.skiko.SystemTheme
import org.jetbrains.skiko.currentSystemTheme

private fun systemIsDark(): Boolean = currentSystemTheme == SystemTheme.DARK

@Composable
fun rememberSystemThemeIsDark(pollMillis: Long = 1_000L): State<Boolean> =
    produceState(systemIsDark(), pollMillis) {
        require(pollMillis > 0) { "Theme polling interval must be positive" }
        while (isActive) {
            value = systemIsDark()
            delay(pollMillis)
        }
    }
