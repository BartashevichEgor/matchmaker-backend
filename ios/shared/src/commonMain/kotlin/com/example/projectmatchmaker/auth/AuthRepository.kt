package com.example.projectmatchmaker.auth

import com.example.projectmatchmaker.network.AuthApi

class AuthRepository(
    private val api: AuthApi = AuthApi(),
) {
    fun hasSavedSession(): Boolean = !TokenStorage.getToken().isNullOrBlank()

    suspend fun login(email: String, password: String): Result<Unit> = authRequest {
        val token = api.login(email, password).accessToken
        require(token.isNotBlank()) { "Сервер вернул пустой токен" }
        TokenStorage.saveToken(token)
    }

    suspend fun register(name: String, email: String, password: String): Result<Unit> = authRequest {
        api.register(name, email, password)

        // После успешной регистрации выполняем вход и сохраняем JWT.
        val token = api.login(email, password).accessToken
        require(token.isNotBlank()) { "Сервер вернул пустой токен" }
        TokenStorage.saveToken(token)
    }

    fun logout() {
        TokenStorage.clearToken()
    }

    fun close() {
        api.close()
    }

    private suspend fun authRequest(block: suspend () -> Unit): Result<Unit> = try {
        block()
        Result.success(Unit)
    } catch (error: Throwable) {
        val technicalMessage = error.message.orEmpty()
        val userMessage = when {
            technicalMessage.contains("timeout", ignoreCase = true) ->
                "Сервер не отвечает. Убедитесь, что backend запущен на порту 8000."

            technicalMessage.contains("failed to connect", ignoreCase = true) ||
                technicalMessage.contains("connection refused", ignoreCase = true) ->
                "Не удалось подключиться к серверу. Проверьте запуск backend."

            else -> technicalMessage.ifBlank { "Не удалось выполнить запрос" }
        }

        Result.failure(IllegalStateException(userMessage, error))
    }
}

