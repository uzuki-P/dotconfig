package example.app.ui

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Card
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Slider
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import example.app.settings.AppSettings
import example.app.settings.ColorSource
import example.app.settings.ThemeMode
import example.app.settings.VibrationStrength

@Composable
fun AppearanceSettings(
    settings: AppSettings,
    onSettingsChange: (AppSettings) -> Unit,
    supportsWallpaper: Boolean = false,
    supportsVibration: Boolean = false,
    onVibrationPreview: (Int) -> Unit = {},
) {
    Column(verticalArrangement = Arrangement.spacedBy(16.dp)) {
        SettingsGroup("Theme") {
            ThemeMode.entries.forEach { mode ->
                Choice(mode.name.lowercase().replaceFirstChar { it.uppercase() }, settings.themeMode == mode) {
                    onSettingsChange(settings.copy(themeMode = mode))
                }
            }
        }
        SettingsGroup("Color") {
            ColorSource.entries.filter { supportsWallpaper || it != ColorSource.WALLPAPER }.forEach { source ->
                Choice(source.name.lowercase().replaceFirstChar { it.uppercase() }, settings.colorSource == source) {
                    onSettingsChange(settings.copy(colorSource = source))
                }
            }
            if (settings.colorSource == ColorSource.CUSTOM) {
                var hex by remember(settings.seedArgb) {
                    mutableStateOf((settings.seedArgb and 0xFFFFFF).toString(16).padStart(6, '0'))
                }
                val rgb = hex.takeIf { value -> value.length == 6 && value.all { it in "0123456789abcdefABCDEF" } }?.toLongOrNull(16)
                OutlinedTextField(
                    value = hex,
                    onValueChange = { hex = it.removePrefix("#") },
                    label = { Text("Seed color, six hex digits") },
                    isError = rgb == null,
                    singleLine = true,
                    modifier = Modifier.fillMaxWidth(),
                )
                TextButton(
                    enabled = rgb != null,
                    onClick = { rgb?.let { onSettingsChange(settings.copy(seedArgb = 0xFF000000L or it)) } },
                ) { Text("Apply color") }
            }
        }
        if (supportsVibration) {
            SettingsGroup("Vibration") {
                VibrationStrength.entries.forEach { strength ->
                    Choice(strength.name.lowercase().replaceFirstChar { it.uppercase() }, settings.vibrationStrength == strength) {
                        val next = settings.copy(vibrationStrength = strength)
                        onSettingsChange(next)
                        onVibrationPreview(next.vibrationMs)
                    }
                }
                if (settings.vibrationStrength == VibrationStrength.CUSTOM) {
                    Text("${settings.vibrationMs} ms")
                    Slider(
                        value = settings.vibrationMs.toFloat(),
                        onValueChange = { onSettingsChange(settings.copy(customVibrationMs = it.toInt())) },
                        valueRange = 1f..200f,
                        onValueChangeFinished = { onVibrationPreview(settings.vibrationMs) },
                    )
                }
            }
        }
    }
}

@Composable
private fun SettingsGroup(title: String, content: @Composable () -> Unit) {
    Card(modifier = Modifier.fillMaxWidth()) {
        Column(Modifier.padding(16.dp)) {
            Text(title, style = MaterialTheme.typography.titleMedium)
            content()
        }
    }
}

@Composable
private fun Choice(label: String, selected: Boolean, onClick: () -> Unit) {
    TextButton(onClick = onClick, modifier = Modifier.fillMaxWidth()) {
        Text(if (selected) "$label, selected" else label)
    }
}
