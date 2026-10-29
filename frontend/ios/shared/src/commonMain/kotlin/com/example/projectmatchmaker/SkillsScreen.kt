package com.example.projectmatchmaker

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp

@Composable
fun SkillsScreen(
    profile: ProfileData,
    onProfileChange: (ProfileData) -> Unit,
    canCreate: Boolean,
    onBack: () -> Unit,
    onCreate: () -> Unit,
    onCatalog: () -> Unit,
) {
    var skillText by remember { mutableStateOf("") }
    var experienceExpanded by remember { mutableStateOf(true) }
    var linksExpanded by remember { mutableStateOf(false) }

    ScreenFrame(MainDestination.PROFILE, onCatalog, {}) {
        PageCard {
            Column(Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(14.dp)) {
                PageTitle("Создание профиля")
                Text("Шаг 2 из 2 · Навыки и опыт", color = MutedTextColor, fontSize = 14.sp)
                StepProgress(1f)

                FormLabel("Навыки *")
                if (profile.skills.isNotEmpty()) {
                    SkillChips(profile.skills) { removed ->
                        onProfileChange(profile.copy(skills = profile.skills - removed))
                    }
                }
                Box(Modifier.padding(top = 8.dp)) {
                    FormField(skillText, { skillText = it }, "Добавить навык")
                    Text(
                        "+",
                        color = PrimaryButtonColor,
                        fontSize = 34.sp,
                        modifier = Modifier.align(Alignment.CenterEnd).clickable {
                            val skill = skillText.trim()
                            if (skill.isNotEmpty() && profile.skills.none { it.equals(skill, true) }) {
                                onProfileChange(profile.copy(skills = profile.skills + skill))
                                skillText = ""
                            }
                        }.padding(horizontal = 15.dp),
                    )
                }
                Text("Нажмите × на навыке, чтобы удалить его", color = MutedTextColor, fontSize = 11.sp)

                ExpandableHeader("Опыт и образование", experienceExpanded) {
                    experienceExpanded = !experienceExpanded
                }
                if (experienceExpanded) {
                    FormLabel("Опыт работы")
                    FormField(
                        profile.experience,
                        { onProfileChange(profile.copy(experience = it)) },
                        "Например, учебные и личные проекты",
                    )
                    FormLabel("Образование")
                    FormField(
                        profile.education,
                        { onProfileChange(profile.copy(education = it)) },
                        "Например, студентка БГУ",
                    )
                }

                ExpandableHeader("GitHub и ссылки", linksExpanded) {
                    linksExpanded = !linksExpanded
                }
                if (linksExpanded) {
                    FormField(
                        profile.github,
                        { onProfileChange(profile.copy(github = it)) },
                        "https://github.com/username",
                    )
                }

                Text(
                    if (canCreate) "Профиль готов к созданию" else "Добавьте хотя бы один навык",
                    color = if (canCreate) MutedTextColor else ErrorColor,
                    fontSize = 11.sp,
                    modifier = Modifier.padding(vertical = 10.dp),
                )
                PrimaryButton("Создать профиль", onCreate, canCreate)
                TextButton(onClick = onBack, contentPadding = PaddingValues(vertical = 8.dp)) {
                    Text("Назад к основному", color = PrimaryButtonColor)
                }
            }
        }
    }
}

@Composable
@Preview
private fun SkillsScreenPreview() {
    MaterialTheme {
        SkillsScreen(ProfileData(), {}, false, {}, {}, {})
    }
}
