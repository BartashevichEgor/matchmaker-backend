package com.example.projectmatchmaker

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.text.input.VisualTransformation
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.ui.tooling.preview.Preview
import kotlinx.coroutines.launch

@Composable
@Preview
fun RegisterScreen(
    onNavigateToLogin: () -> Unit = {},
    onRegister: suspend (name: String, email: String, password: String) -> Result<Unit> = { _, _, _ -> Result.success(Unit) },
    onAuthenticated: () -> Unit = {},
) {
    var userName by remember { mutableStateOf("") }
    var email by remember { mutableStateOf("") }
    var password by remember { mutableStateOf("") }
    var confirmPassword by remember { mutableStateOf("") }

    var isPasswordVisible by remember { mutableStateOf(false) }
    var isConfirmPasswordVisible by remember { mutableStateOf(false) }
    var isLoading by remember { mutableStateOf(false) }
    var serverError by remember { mutableStateOf<String?>(null) }
    val scope = rememberCoroutineScope()

    // Валидация
    val isNameValid = userName.isEmpty() || userName.length >= 2
    val isEmailValid = email.isEmpty() || (email.contains("@") && email.contains("."))
    val isPasswordValid = password.isEmpty() || password.length >= 6
    val doPasswordsMatch = confirmPassword.isEmpty() || password == confirmPassword

    val canRegister = userName.isNotBlank() && email.isNotBlank() && password.isNotBlank() && confirmPassword.isNotBlank() &&
            isNameValid && isEmailValid && isPasswordValid && doPasswordsMatch

    Box(
        modifier = Modifier
            .fillMaxSize()
            .background(DarkBgColor),
        contentAlignment = Alignment.Center
    ) {
        Column(
            horizontalAlignment = Alignment.CenterHorizontally,
            modifier = Modifier.padding(24.dp)
        ) {
            Text(
                text = "Matchmaker",
                color = CardBgColor,
                fontSize = 28.sp,
                fontWeight = FontWeight.Bold,
                modifier = Modifier.padding(bottom = 20.dp)
            )

            Surface(
                shape = RoundedCornerShape(28.dp),
                color = CardBgColor,
                modifier = Modifier.fillMaxWidth()
            ) {
                Column(
                    modifier = Modifier.padding(24.dp),
                    horizontalAlignment = Alignment.CenterHorizontally
                ) {
                    Text(
                        text = "Регистрация",
                        fontSize = 22.sp,
                        fontWeight = FontWeight.Bold,
                        color = TextDarkColor,
                        modifier = Modifier.padding(bottom = 16.dp)
                    )

                    // Имя
                    Column(modifier = Modifier.fillMaxWidth()) {
                        Text(
                            text = "Имя пользователя",
                            fontSize = 12.sp,
                            color = TextDarkColor,
                            modifier = Modifier.padding(bottom = 4.dp)
                        )
                        OutlinedTextField(
                            value = userName,
                            onValueChange = { userName = it },
                            placeholder = { Text("username", color = Color.Gray) },
                            singleLine = true,
                            isError = !isNameValid,
                            colors = OutlinedTextFieldDefaults.colors(
                                focusedContainerColor = Color.White,
                                unfocusedContainerColor = Color.White,
                                errorContainerColor = Color(0xFFFDE8E8),
                                focusedBorderColor = TextDarkColor,
                                unfocusedBorderColor = Color.Transparent,
                                errorBorderColor = ErrorColor
                            ),
                            shape = RoundedCornerShape(12.dp),
                            modifier = Modifier.fillMaxWidth()
                        )
                        if (!isNameValid) {
                            Text(
                                text = "Имя пользователя должно быть не короче 2 символов",
                                color = ErrorColor,
                                fontSize = 11.sp,
                                modifier = Modifier.padding(top = 4.dp, start = 4.dp)
                            )
                        }
                    }

                    Spacer(modifier = Modifier.height(10.dp))

                    // E-mail
                    Column(modifier = Modifier.fillMaxWidth()) {
                        Text(
                            text = "E-mail",
                            fontSize = 12.sp,
                            color = TextDarkColor,
                            modifier = Modifier.padding(bottom = 4.dp)
                        )
                        OutlinedTextField(
                            value = email,
                            onValueChange = { email = it },
                            placeholder = { Text("you@example.com", color = Color.Gray) },
                            singleLine = true,
                            isError = !isEmailValid,
                            trailingIcon = {
                                if (!isEmailValid) {
                                    Text("❗", fontSize = 14.sp)
                                }
                            },
                            colors = OutlinedTextFieldDefaults.colors(
                                focusedContainerColor = Color.White,
                                unfocusedContainerColor = Color.White,
                                errorContainerColor = Color(0xFFFDE8E8),
                                focusedBorderColor = TextDarkColor,
                                unfocusedBorderColor = Color.Transparent,
                                errorBorderColor = ErrorColor
                            ),
                            shape = RoundedCornerShape(12.dp),
                            keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Email),
                            modifier = Modifier.fillMaxWidth()
                        )
                        if (!isEmailValid) {
                            Text(
                                text = "Введите корректный e-mail",
                                color = ErrorColor,
                                fontSize = 11.sp,
                                modifier = Modifier.padding(top = 4.dp, start = 4.dp)
                            )
                        }
                    }

                    Spacer(modifier = Modifier.height(10.dp))

                    // Пароль
                    Column(modifier = Modifier.fillMaxWidth()) {
                        Text(
                            text = "Пароль",
                            fontSize = 12.sp,
                            color = TextDarkColor,
                            modifier = Modifier.padding(bottom = 4.dp)
                        )
                        OutlinedTextField(
                            value = password,
                            onValueChange = { password = it },
                            placeholder = { Text("••••••••", color = Color.Gray) },
                            singleLine = true,
                            visualTransformation = if (isPasswordVisible) VisualTransformation.None else PasswordVisualTransformation(),
                            trailingIcon = {
                                IconButton(onClick = { isPasswordVisible = !isPasswordVisible }) {
                                    Text(if (isPasswordVisible) "👁" else "🙈")
                                }
                            },
                            colors = OutlinedTextFieldDefaults.colors(
                                focusedContainerColor = Color.White,
                                unfocusedContainerColor = Color.White,
                                focusedBorderColor = TextDarkColor,
                                unfocusedBorderColor = Color.Transparent
                            ),
                            shape = RoundedCornerShape(12.dp),
                            keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Password),
                            modifier = Modifier.fillMaxWidth()
                        )
                    }

                    Spacer(modifier = Modifier.height(10.dp))

                    // Подтвердите пароль
                    Column(modifier = Modifier.fillMaxWidth()) {
                        Text(
                            text = "Подтвердите пароль",
                            fontSize = 12.sp,
                            color = TextDarkColor,
                            modifier = Modifier.padding(bottom = 4.dp)
                        )
                        OutlinedTextField(
                            value = confirmPassword,
                            onValueChange = { confirmPassword = it },
                            placeholder = { Text("••••••••", color = Color.Gray) },
                            singleLine = true,
                            isError = !doPasswordsMatch,
                            visualTransformation = if (isConfirmPasswordVisible) VisualTransformation.None else PasswordVisualTransformation(),
                            trailingIcon = {
                                if (!doPasswordsMatch) {
                                    Text("❗", fontSize = 14.sp)
                                } else {
                                    IconButton(onClick = { isConfirmPasswordVisible = !isConfirmPasswordVisible }) {
                                        Text(if (isConfirmPasswordVisible) "👁" else "🙈")
                                    }
                                }
                            },
                            colors = OutlinedTextFieldDefaults.colors(
                                focusedContainerColor = Color.White,
                                unfocusedContainerColor = Color.White,
                                errorContainerColor = Color(0xFFFDE8E8),
                                focusedBorderColor = TextDarkColor,
                                unfocusedBorderColor = Color.Transparent,
                                errorBorderColor = ErrorColor
                            ),
                            shape = RoundedCornerShape(12.dp),
                            keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Password),
                            modifier = Modifier.fillMaxWidth()
                        )
                        if (!doPasswordsMatch) {
                            Text(
                                text = "Пароли не совпадают",
                                color = ErrorColor,
                                fontSize = 11.sp,
                                modifier = Modifier.padding(top = 4.dp, start = 4.dp)
                            )
                        }
                    }

                    Spacer(modifier = Modifier.height(20.dp))

                    // Кнопка Зарегистрироваться
                    Button(
                        onClick = {
                            serverError = null
                            scope.launch {
                                isLoading = true
                                val result = onRegister(userName, email, password)
                                isLoading = false

                                result.onSuccess { onAuthenticated() }
                                    .onFailure { serverError = it.message ?: "Не удалось зарегистрироваться" }
                            }
                        },
                        enabled = canRegister && !isLoading,
                        colors = ButtonDefaults.buttonColors(
                            containerColor = PrimaryButtonColor,
                            disabledContainerColor = DisabledButtonColor,
                            contentColor = Color.White,
                            disabledContentColor = Color.White.copy(alpha = 0.8f)
                        ),
                        shape = RoundedCornerShape(12.dp),
                        modifier = Modifier
                            .fillMaxWidth()
                            .height(48.dp)
                    ) {
                        if (isLoading) {
                            CircularProgressIndicator(
                                modifier = Modifier.size(22.dp),
                                color = Color.White,
                                strokeWidth = 2.dp,
                            )
                        } else {
                            Text("Зарегистрироваться", fontSize = 16.sp, fontWeight = FontWeight.Bold)
                        }
                    }

                    serverError?.let { message ->
                        Text(
                            text = message,
                            color = ErrorColor,
                            fontSize = 12.sp,
                            modifier = Modifier.padding(top = 8.dp),
                        )
                    }

                    Spacer(modifier = Modifier.height(16.dp))

                    // Переход на вход
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Text(
                            text = "Уже есть аккаунт? ",
                            fontSize = 13.sp,
                            color = TextDarkColor
                        )
                        TextButton(
                            onClick = onNavigateToLogin,
                            contentPadding = PaddingValues(0.dp)
                        ) {
                            Text(
                                text = "Войти",
                                fontSize = 13.sp,
                                fontWeight = FontWeight.Bold,
                                color = TextDarkColor
                            )
                        }
                    }
                }
            }
        }
    }
}
