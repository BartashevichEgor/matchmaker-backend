package com.example.projectmatchmaker

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp

@Composable
fun CreateProfileScreen(
    profile: ProfileData,
    onProfileChange: (ProfileData) -> Unit,
    canContinue: Boolean,
    onNext: () -> Unit,
    onCatalog: () -> Unit,
) {
    ScreenFrame(MainDestination.PROFILE, onCatalog, {}) {
        PageCard {
            Column(
                Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(14.dp),
            ) {
                PageTitle("Создание профиля")
                Text("Шаг 1 из 2 · Основное", color = MutedTextColor, fontSize = 14.sp)
                StepProgress(0.5f)
                PhotoPicker()

                FormLabel("Имя и фамилия *")
                FormField(profile.name, { onProfileChange(profile.copy(name = it)) }, "Например, Алина Иванова")

                FormLabel("Роль *")
                FormField(profile.role, { onProfileChange(profile.copy(role = it)) }, "Например, iOS-разработчик")

                FormLabel("О себе")
                FormField(
                    profile.about,
                    { onProfileChange(profile.copy(about = it)) },
                    "Расскажите, чем вы занимаетесь и какой проект ищете",
                    minLines = 3,
                )

                if (!canContinue) {
                    Text(
                        "Заполните имя (минимум 2 символа) и роль",
                        color = ErrorColor,
                        fontSize = 11.sp,
                        modifier = Modifier.padding(top = 8.dp),
                    )
                } else {
                    Text(
                        "* Обязательные поля заполнены",
                        color = MutedTextColor,
                        fontSize = 11.sp,
                        modifier = Modifier.padding(top = 8.dp),
                    )
                }

                Spacer(Modifier.size(8.dp))
                PrimaryButton("Далее: навыки и опыт", onNext, canContinue)
                Spacer(Modifier.size(12.dp))
            }
        }
    }
}

@Composable
private fun PhotoPicker() {
    Row(Modifier.padding(vertical = 20.dp), verticalAlignment = Alignment.CenterVertically) {
        Box(
            Modifier.size(64.dp).background(SectionBgColor, CircleShape),
            contentAlignment = Alignment.Center,
        ) {
            Text("+", color = PrimaryButtonColor, fontSize = 34.sp, fontWeight = FontWeight.Light)
        }
        Spacer(Modifier.size(16.dp))
        Column {
            Text("Добавить фото", color = PrimaryButtonColor, fontSize = 16.sp, fontWeight = FontWeight.Bold)
            Text("Можно заполнить позже", color = MutedTextColor, fontSize = 13.sp)
        }
    }
}

@Composable
@Preview
private fun CreateProfileScreenPreview() {
    MaterialTheme {
        CreateProfileScreen(ProfileData(), {}, false, {}, {})
    }
}
