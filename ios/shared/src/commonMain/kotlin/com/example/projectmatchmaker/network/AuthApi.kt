package com.example.projectmatchmaker.network

import io.ktor.client.HttpClient
import io.ktor.client.call.body
import io.ktor.client.plugins.contentnegotiation.ContentNegotiation
import io.ktor.client.request.post
import io.ktor.client.request.setBody
import io.ktor.client.statement.bodyAsText
import io.ktor.http.ContentType
import io.ktor.http.contentType
import io.ktor.http.isSuccess
import io.ktor.serialization.kotlinx.json.json
import kotlinx.serialization.json.Json

class AuthApi(
    private val baseUrl: String = platformApiBaseUrl(),
) {
    private val json = Json {
        ignoreUnknownKeys = true
        isLenient = true
    }

    private val client = HttpClient {
        expectSuccess = false
        install(ContentNegotiation) {
            json(json)
        }
    }

    suspend fun login(email: String, password: String): TokenResponse {
        val response = client.post("$baseUrl/auth/login") {
            contentType(ContentType.Application.Json)
            setBody(LoginRequest(email = email.trim(), password = password))
        }

        if (!response.status.isSuccess()) {
            throw ApiException(readError(response.bodyAsText(), response.status.value))
        }

        return response.body()
    }

    suspend fun register(name: String, email: String, password: String) {
        val response = client.post("$baseUrl/auth/register") {
            contentType(ContentType.Application.Json)
            setBody(
                RegisterRequest(
                    username = name.trim(),
                    email = email.trim(),
                    password = password,
                )
            )
        }

        if (!response.status.isSuccess()) {
            throw ApiException(readError(response.bodyAsText(), response.status.value))
        }
    }

    suspend fun verifyEmail(email: String, code: String) {
        val response = client.post("$baseUrl/auth/verify-email") {
            contentType(ContentType.Application.Json)
            setBody(VerifyEmailRequest(email = email.trim(), code = code.trim()))
        }

        if (!response.status.isSuccess()) {
            throw ApiException(readError(response.bodyAsText(), response.status.value))
        }
    }

    fun close() {
        client.close()
    }

    private fun readError(body: String, statusCode: Int): String {
        val serverMessage = runCatching {
            val error = json.decodeFromString<ApiErrorResponse>(body)
            error.detail ?: error.message
        }.getOrNull()

        return serverMessage ?: "Ошибка сервера ($statusCode)"
    }
}

class ApiException(message: String) : Exception(message)

