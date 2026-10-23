package com.example.projectmatchmaker.auth

expect object TokenStorage {
    fun saveToken(token: String)
    fun getToken(): String?
    fun clearToken()
}

