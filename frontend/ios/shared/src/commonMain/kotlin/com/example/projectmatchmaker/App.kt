package com.example.projectmatchmaker

import androidx.compose.material3.MaterialTheme
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.tooling.preview.Preview

private enum class AppScreen {
    LOGIN,
    REGISTER,
    CREATE_PROFILE,
    ADD_SKILLS,
    PROFILE,
    CATALOG,
}

/**
 * Локальная навигация прототипа. Backend здесь намеренно не используется:
 * введённые данные живут в состоянии App и передаются между экранами.
 */
@Composable
fun App() {
    var screen by remember { mutableStateOf(AppScreen.LOGIN) }
    var profile by remember { mutableStateOf(ProfileData()) }

    val basicProfileIsValid = profile.name.trim().length >= 2 && profile.role.isNotBlank()
    val skillsAreValid = profile.skills.isNotEmpty()

    MaterialTheme {
        when (screen) {
            AppScreen.LOGIN -> LoginScreen(
                onLogin = { email, _ ->
                    profile = profile.copy(email = email.trim())
                    Result.success(Unit)
                },
                onAuthenticated = { screen = AppScreen.CREATE_PROFILE },
                onNavigateToRegister = { screen = AppScreen.REGISTER },
            )

            AppScreen.REGISTER -> RegisterScreen(
                onRegister = { name, email, _ ->
                    profile = profile.copy(name = name.trim(), email = email.trim())
                    Result.success(Unit)
                },
                onAuthenticated = { screen = AppScreen.CREATE_PROFILE },
                onNavigateToLogin = { screen = AppScreen.LOGIN },
            )

            AppScreen.CREATE_PROFILE -> CreateProfileScreen(
                profile = profile,
                onProfileChange = { profile = it },
                canContinue = basicProfileIsValid,
                onNext = { if (basicProfileIsValid) screen = AppScreen.ADD_SKILLS },
                onCatalog = { screen = AppScreen.CATALOG },
            )

            AppScreen.ADD_SKILLS -> SkillsScreen(
                profile = profile,
                onProfileChange = { profile = it },
                canCreate = skillsAreValid,
                onBack = { screen = AppScreen.CREATE_PROFILE },
                onCreate = { if (skillsAreValid) screen = AppScreen.PROFILE },
                onCatalog = { screen = AppScreen.CATALOG },
            )

            AppScreen.PROFILE -> ProfileScreen(
                profile = profile,
                onEdit = { screen = AppScreen.CREATE_PROFILE },
                onCatalog = { screen = AppScreen.CATALOG },
                onLogout = {
                    profile = ProfileData()
                    screen = AppScreen.LOGIN
                },
            )

            AppScreen.CATALOG -> CatalogScreen(
                onCatalog = { screen = AppScreen.CATALOG },
                onProfile = {
                    screen = if (basicProfileIsValid && skillsAreValid) {
                        AppScreen.PROFILE
                    } else {
                        AppScreen.CREATE_PROFILE
                    }
                },
            )
        }
    }
}

@Composable
@Preview
private fun AppPreview() {
    MaterialTheme { App() }
}
