package example.app.settings

enum class ThemeMode { SYSTEM, LIGHT, DARK }
enum class ColorSource { DEFAULT, WALLPAPER, CUSTOM }
enum class VibrationStrength { OFF, LIGHT, DEFAULT, STRONG, CUSTOM }

data class AppSettings(
    val themeMode: ThemeMode = ThemeMode.SYSTEM,
    val colorSource: ColorSource = ColorSource.DEFAULT,
    val seedArgb: Long = 0xFF6750A4,
    val vibrationStrength: VibrationStrength = VibrationStrength.DEFAULT,
    val customVibrationMs: Int = 25,
) {
    val vibrationMs: Int
        get() = when (vibrationStrength) {
            VibrationStrength.OFF -> 0
            VibrationStrength.LIGHT -> 12
            VibrationStrength.DEFAULT -> 25
            VibrationStrength.STRONG -> 50
            VibrationStrength.CUSTOM -> customVibrationMs.coerceIn(1, 200)
        }

    fun isDark(systemDark: Boolean): Boolean = when (themeMode) {
        ThemeMode.SYSTEM -> systemDark
        ThemeMode.LIGHT -> false
        ThemeMode.DARK -> true
    }
}

inline fun <reified T : Enum<T>> storedEnum(value: String?, fallback: T): T =
    enumValues<T>().firstOrNull { it.name == value } ?: fallback
