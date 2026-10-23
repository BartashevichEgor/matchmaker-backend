package com.example.projectmatchmaker

import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.StrokeCap
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp

private enum class CatalogTab { PROJECTS, PEOPLE }

@Composable
fun CatalogScreen(onCatalog: () -> Unit, onProfile: () -> Unit) {
    var tab by remember { mutableStateOf(CatalogTab.PEOPLE) }

    ScreenFrame(MainDestination.CATALOG, onCatalog, onProfile) {
        PageCard {
            Column(Modifier.fillMaxSize().padding(14.dp)) {
                Row(
                    Modifier.fillMaxWidth(),
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.SpaceBetween,
                ) {
                    PageTitle("Каталог")
                    FilterIcon()
                }
                CatalogTabs(tab) { tab = it }
                Spacer(Modifier.height(16.dp))
                Column(Modifier.weight(1f).verticalScroll(rememberScrollState())) {
                    if (tab == CatalogTab.PEOPLE) PersonCatalogCard() else ProjectCatalogCard()
                }
                SwipeActions()
            }
        }
    }
}

@Composable
private fun CatalogTabs(selected: CatalogTab, onSelect: (CatalogTab) -> Unit) {
    Row(Modifier.fillMaxWidth().background(SectionBgColor, RoundedCornerShape(12.dp)).padding(3.dp)) {
        CatalogTabButton("Проекты", selected == CatalogTab.PROJECTS, Modifier.weight(1f)) { onSelect(CatalogTab.PROJECTS) }
        CatalogTabButton("Специалисты", selected == CatalogTab.PEOPLE, Modifier.weight(1f)) { onSelect(CatalogTab.PEOPLE) }
    }
}

@Composable
private fun CatalogTabButton(text: String, selected: Boolean, modifier: Modifier, onClick: () -> Unit) {
    Box(
        modifier.height(42.dp)
            .background(if (selected) PrimaryButtonColor else Color.Transparent, RoundedCornerShape(10.dp))
            .clickable(onClick = onClick),
        contentAlignment = Alignment.Center,
    ) {
        Text(text, color = if (selected) CardBgColor else TextDarkColor, fontWeight = FontWeight.Bold)
    }
}

@Composable
private fun PersonCatalogCard() {
    Surface(color = Color(0xFFF6EDCC), shape = RoundedCornerShape(24.dp)) {
        Column(Modifier.padding(16.dp)) {
            Box(
                Modifier.fillMaxWidth().height(178.dp).background(ProfileAvatarColor, RoundedCornerShape(18.dp)),
                contentAlignment = Alignment.Center,
            ) {
                Surface(color = CardBgColor, shape = CircleShape, modifier = Modifier.size(82.dp)) {
                    Box(contentAlignment = Alignment.Center) {
                        Text("АК", color = PrimaryButtonColor, fontSize = 32.sp, fontWeight = FontWeight.Bold)
                    }
                }
                Surface(
                    color = PrimaryButtonColor,
                    shape = RoundedCornerShape(18.dp),
                    modifier = Modifier.align(Alignment.TopCenter).padding(top = 12.dp),
                ) {
                    Text("87% совпадение", color = Color.White, fontSize = 12.sp, modifier = Modifier.padding(horizontal = 14.dp, vertical = 6.dp))
                }
            }
            Text("Алексей Ковалёв", color = TextDarkColor, fontSize = 25.sp, fontWeight = FontWeight.Bold, modifier = Modifier.padding(top = 16.dp))
            Text("Backend-разработчик", color = MutedTextColor, fontSize = 17.sp, modifier = Modifier.padding(vertical = 6.dp))
            SkillChips(listOf("Python", "Django", "SQL"))
            Text("Люблю чистый код. Ищу команду для полезного проекта.", color = TextDarkColor, fontSize = 16.sp, lineHeight = 21.sp, modifier = Modifier.padding(top = 12.dp))
        }
    }
    ExpandableHeader("Опыт и GitHub", false) { }
}

@Composable
private fun ProjectCatalogCard() {
    Surface(color = Color(0xFFF6EDCC), shape = RoundedCornerShape(24.dp)) {
        Column(Modifier.padding(16.dp)) {
            Box(
                Modifier.fillMaxWidth().height(145.dp).background(SectionBgColor, RoundedCornerShape(18.dp)).padding(20.dp),
                contentAlignment = Alignment.CenterStart,
            ) {
                Column {
                    Text("TeamFlow", color = PrimaryButtonColor, fontSize = 34.sp, fontWeight = FontWeight.Bold)
                    Text("Сервис для студенческих команд", color = TextDarkColor, fontSize = 15.sp, modifier = Modifier.padding(top = 8.dp))
                }
            }
            Text("TeamFlow", color = TextDarkColor, fontSize = 25.sp, fontWeight = FontWeight.Bold, modifier = Modifier.padding(top = 16.dp))
            Text("Ищем UI/UX-дизайнера", color = MutedTextColor, fontSize = 17.sp, modifier = Modifier.padding(vertical = 6.dp))
            SkillChips(listOf("Figma", "UX", "UI"))
            Text("Создаём планировщик задач. Нужна помощь с интерфейсом и прототипом.", color = TextDarkColor, fontSize = 16.sp, lineHeight = 21.sp, modifier = Modifier.padding(top = 12.dp))
        }
    }
    ExpandableHeader("Подробнее о проекте", false) { }
}

@Composable
private fun SwipeActions() {
    Row(
        Modifier.fillMaxWidth().padding(vertical = 12.dp),
        horizontalArrangement = Arrangement.Center,
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Surface(
            modifier = Modifier.size(60.dp).clickable { },
            color = CardBgColor,
            shape = CircleShape,
            border = BorderStroke(1.dp, MutedTextColor),
        ) {
            Box(contentAlignment = Alignment.Center) {
                Text("×", color = PrimaryButtonColor, fontSize = 38.sp, fontWeight = FontWeight.Light)
            }
        }
        Spacer(Modifier.size(36.dp))
        Surface(Modifier.size(66.dp).clickable { }, color = PrimaryButtonColor, shape = CircleShape) {
            Box(contentAlignment = Alignment.Center) { Text("♡", color = CardBgColor, fontSize = 38.sp) }
        }
    }
}

@Composable
private fun FilterIcon() {
    Canvas(Modifier.size(30.dp)) {
        val stroke = 2.dp.toPx()
        listOf(7f, 14f, 21f).forEachIndexed { index, y ->
            drawLine(PrimaryButtonColor, Offset(3.dp.toPx(), y.dp.toPx()), Offset(27.dp.toPx(), y.dp.toPx()), stroke, StrokeCap.Round)
            val x = listOf(10, 20, 13)[index].dp.toPx()
            drawCircle(PrimaryButtonColor, 3.dp.toPx(), Offset(x, y.dp.toPx()))
        }
    }
}

@Composable
@Preview
private fun CatalogScreenPreview() {
    MaterialTheme { CatalogScreen({}, {}) }
}
