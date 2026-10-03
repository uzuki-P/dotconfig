package example.app.settings

import java.util.prefs.Preferences
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.sync.Mutex
import kotlinx.coroutines.sync.withLock
import kotlinx.coroutines.withContext

// Supply the target app's stable preference node, not a user-specific path.
class DesktopSettingsStore(node: String) {
    private val preferences = Preferences.userRoot().node(node)
    private val writes = Mutex()
    private val state = MutableStateFlow(
        AppSettings(
            themeMode = storedEnum(preferences.get("theme_mode", null), ThemeMode.SYSTEM),
            colorSource = storedEnum(preferences.get("color_source", null), ColorSource.DEFAULT),
            seedArgb = preferences.getLong("seed_argb", AppSettings().seedArgb),
            vibrationStrength = VibrationStrength.OFF,
        )
    )
    val settings: StateFlow<AppSettings> = state.asStateFlow()

    suspend fun save(settings: AppSettings) = writes.withLock {
        withContext(Dispatchers.IO) {
            preferences.put("theme_mode", settings.themeMode.name)
            preferences.put("color_source", settings.colorSource.name)
            preferences.putLong("seed_argb", settings.seedArgb)
            preferences.flush()
            state.value = settings.copy(vibrationStrength = VibrationStrength.OFF)
        }
    }
}
