package com.example.projectmatchmaker.auth

actual object TokenStorage {
    private var token: String? = null

    actual fun saveToken(token: String) {
        this.token = token
    }

    actual fun getToken(): String? = token

    actual fun clearToken() {
        token = null
    }
}

