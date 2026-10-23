package com.example.projectmatchmaker.network

import kotlin.test.Test
import kotlin.test.assertEquals
import kotlinx.serialization.encodeToString
import kotlinx.serialization.json.Json

class AuthModelsTest {
    private val json = Json { ignoreUnknownKeys = true }

    @Test
    fun loginRequestIsConvertedToJson() {
        val encoded = json.encodeToString(
            LoginRequest(email = "alina@example.com", password = "secret123")
        )

        assertEquals(
            "{\"email\":\"alina@example.com\",\"password\":\"secret123\"}",
            encoded,
        )
    }

    @Test
    fun tokenResponseReadsSnakeCaseFields() {
        val response = json.decodeFromString<TokenResponse>(
            """{"access_token":"jwt-value","token_type":"bearer","expires_in":3600}"""
        )

        assertEquals("jwt-value", response.accessToken)
        assertEquals("bearer", response.tokenType)
    }
}

