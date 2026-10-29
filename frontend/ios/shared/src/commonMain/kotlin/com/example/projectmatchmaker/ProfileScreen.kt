package com.example.projectmatchmaker

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp

@Composable
fun ProfileScreen(
    profile: ProfileData,
    onEdit: () -> Unit,
    onLogout: () -> Unit,
    onCatalog: () -> Unit,
) {
    var experienceExpanded by remember { mutableStateOf(false) }
    var linksExpanded by remember { mutableStateOf(false) }

    ScreenFrame(MainDestination.PROFILE, onCatalog, {}) {
        PageCard {
            Column(Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(14.dp)) {
                PageTitle("Мой профиль")

                Box(Modifier.fillMaxWidth(), contentAlignment = Alignment.Center) {
                    Column(horizontalAlignment = Alignment.CenterHorizontally) {
                        Box(
                            Modifier.size(92.dp).background(ProfileAvatarColor, CircleShape),
                            contentAlignment = Alignment.Center,
                        ) {
                            Text(initials(profile.name), color = CardBgColor, fontSize = 30.sp, fontWeight = FontWeight.Bold)
                        }
                        Text(
                            "@${profile.username}",
                            color = TextDarkColor,
                            fontSize = 25.sp,
                            fontWeight = FontWeight.Bold,
                            modifier = Modifier.padding(top = 10.dp),
                        )
                        Text(profile.name, color = TextDarkColor, fontSize = 16.sp)
                        Text(profile.role, color = MutedTextColor, fontSize = 17.sp)
                    }
                }

                Row(
                    Modifier.fillMaxWidth().padding(top = 18.dp),
                    horizontalArrangement = Arrangement.spacedBy(12.dp),
                ) {
                    StatCard("0", "мэтчей", Modifier.weight(1f))
                    StatCard("0", "лайков", Modifier.weight(1f))
                }

                FormLabel("О себе")
                Text(
                    profile.about.ifBlank { "Описание пока не заполнено" },
                    color = if (profile.about.isBlank()) MutedTextColor else TextDarkColor,
                    fontSize = 16.sp,
                    lineHeight = 21.sp,
                )

                FormLabel("Стек и навыки")
                SkillChips(profile.skills)

                ExpandableHeader("Опыт и образование", experienceExpanded) {
                    experienceExpanded = !experienceExpanded
                }
                if (experienceExpanded) {
                    ProfileValue("Опыт", profile.experience)
                    ProfileValue("Образование", profile.education)
                }

                ExpandableHeader("GitHub и ссылки", linksExpanded) {
                    linksExpanded = !linksExpanded
                }
                if (linksExpanded) {
                    ProfileValue("GitHub", profile.github)
                }

                Spacer(Modifier.height(12.dp))
                PrimaryButton("Редактировать профиль", onEdit)
                TextButton(onClick = onLogout, modifier = Modifier.align(Alignment.CenterHorizontally)) {
                    Text("Вернуться к экрану входа", color = MutedTextColor, fontSize = 12.sp)
                }
            }
        }
    }
}

@Composable
private fun ProfileValue(label: String, value: String) {
    Column(Modifier.padding(horizontal = 12.dp, vertical = 6.dp)) {
        Text(label, color = TextDarkColor, fontWeight = FontWeight.Bold, fontSize = 13.sp)
        Text(value.ifBlank { "Не указано" }, color = MutedTextColor, fontSize = 14.sp)
    }
}

@Composable
private fun StatCard(value: String, label: String, modifier: Modifier = Modifier) {
    Surface(modifier, color = SectionBgColor, shape = RoundedCornerShape(15.dp)) {
        Column(Modifier.padding(horizontal = 14.dp, vertical = 12.dp)) {
            Text(value, color = TextDarkColor, fontSize = 25.sp, fontWeight = FontWeight.Bold)
            Text(label, color = MutedTextColor, fontSize = 13.sp)
        }
    }
}

private val previewProfile = ProfileData(
    name = "Алина Иванова",
    email = "alina@example.com",
    role = "iOS-разработчик",
    about = "Разрабатываю мобильные интерфейсы на Kotlin и Compose Multiplatform.",
    skills = listOf("Kotlin", "KMP", "Figma"),
    experience = "Учебный проект Project Matchmaker",
    education = "Студентка",
    github = "https://github.com/alina",
)

@Composable
@Preview
private fun ProfileScreenPreview() {
    MaterialTheme { ProfileScreen(previewProfile, {}, {}, {}) }
}
