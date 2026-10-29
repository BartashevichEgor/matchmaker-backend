package com.example.projectmatchmaker.network

/**
 * Для Android-эмулятора localhost компьютера доступен как 10.0.2.2.
 * Когда backend будет опубликован, замените значение actual-функций на HTTPS URL сервера.
 */
expect fun platformApiBaseUrl(): String

