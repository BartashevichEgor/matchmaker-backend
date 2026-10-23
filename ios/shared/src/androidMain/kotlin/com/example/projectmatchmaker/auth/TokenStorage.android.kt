package com.example.projectmatchmaker.auth

import android.content.Context
import android.content.SharedPreferences
import androidx.security.crypto.EncryptedSharedPreferences
import androidx.security.crypto.MasterKey

actual object TokenStorage {
    private const val FILE_NAME = "secure_auth"
    private const val TOKEN_KEY = "jwt_access_token"

    private var preferences: SharedPreferences? = null

    @Suppress("DEPRECATION")
    fun initialize(context: Context) {
        if (preferences != null) return

        val masterKey = MasterKey.Builder(context.applicationContext)
            .setKeyScheme(MasterKey.KeyScheme.AES256_GCM)
            .build()

        preferences = EncryptedSharedPreferences.create(
            context.applicationContext,
            FILE_NAME,
            masterKey,
            EncryptedSharedPreferences.PrefKeyEncryptionScheme.AES256_SIV,
            EncryptedSharedPreferences.PrefValueEncryptionScheme.AES256_GCM,
        )
    }

    actual fun saveToken(token: String) {
        checkNotNull(preferences) { "TokenStorage.initialize() должен быть вызван при запуске Android" }
            .edit()
            .putString(TOKEN_KEY, token)
            .apply()
    }

    actual fun getToken(): String? = preferences?.getString(TOKEN_KEY, null)

    actual fun clearToken() {
        preferences?.edit()?.remove(TOKEN_KEY)?.apply()
    }
}

