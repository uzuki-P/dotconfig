package example.app.settings

import android.content.Context
import androidx.datastore.preferences.core.edit
import androidx.datastore.preferences.core.intPreferencesKey
import androidx.datastore.preferences.core.longPreferencesKey
import androidx.datastore.preferences.core.stringPreferencesKey
import androidx.datastore.preferences.preferencesDataStore
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map

private val Context.appearanceStore by preferencesDataStore(name = "appearance")

class AndroidSettingsStore(context: Context) {
    private val store = context.applicationContext.appearanceStore
    private val theme = stringPreferencesKey("theme_mode")
    private val color = stringPreferencesKey("color_source")
    private val seed = longPreferencesKey("seed_argb")
    private val vibration = stringPreferencesKey("vibration_strength")
    private val duration = intPreferencesKey("custom_vibration_ms")

    val settings: Flow<AppSettings> = store.data.map { values ->
        AppSettings(
            themeMode = storedEnum(values[theme], ThemeMode.SYSTEM),
            colorSource = storedEnum(values[color], ColorSource.DEFAULT),
            seedArgb = values[seed] ?: AppSettings().seedArgb,
            vibrationStrength = storedEnum(values[vibration], VibrationStrength.DEFAULT),
            customVibrationMs = (values[duration] ?: 25).coerceIn(1, 200),
        )
    }

    suspend fun save(settings: AppSettings) {
        store.edit { values ->
            values[theme] = settings.themeMode.name
            values[color] = settings.colorSource.name
            values[seed] = settings.seedArgb
            values[vibration] = settings.vibrationStrength.name
            values[duration] = settings.customVibrationMs.coerceIn(1, 200)
        }
    }
}
