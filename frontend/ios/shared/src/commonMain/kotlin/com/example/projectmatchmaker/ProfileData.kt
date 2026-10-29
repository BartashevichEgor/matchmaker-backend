package com.example.projectmatchmaker

data class ProfileData(
    val name: String = "",
    val email: String = "",
    val role: String = "",
    val about: String = "",
    val skills: List<String> = emptyList(),
    val experience: String = "",
    val education: String = "",
    val github: String = "",
) {
    val username: String
        get() = email.substringBefore("@").ifBlank {
            name.trim().substringBefore(" ").lowercase().ifBlank { "user" }
        }
}
