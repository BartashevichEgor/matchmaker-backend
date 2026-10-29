package com.example.projectmatchmaker

interface Platform {
    val name: String
}

expect fun getPlatform(): Platform