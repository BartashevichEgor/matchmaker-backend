package com.example.projectmatchmaker

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
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TextFieldDefaults
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.StrokeCap
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.ImeAction
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp

enum class MainDestination { CATALOG, PROFILE }

@Composable
fun ScreenFrame(
    selected: MainDestination,
    onCatalog: () -> Unit,
    onProfile: () -> Unit,
    content: @Composable () -> Unit,
) {
    Column(Modifier.fillMaxSize().background(DarkBgColor)) {
        BrandHeader()
        Box(Modifier.weight(1f)) { content() }
        BottomNavigation(selected, onCatalog, onProfile)
    }
}

@Composable
private fun BrandHeader() {
    Row(
        Modifier.fillMaxWidth().height(86.dp).padding(horizontal = 24.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        BrandMark()
        Spacer(Modifier.size(10.dp))
        Text("Matchmaker", color = CardBgColor, fontSize = 25.sp, fontWeight = FontWeight.Bold)
    }
}

@Composable
private fun BrandMark() {
    Canvas(Modifier.size(width = 35.dp, height = 28.dp)) {
        val stroke = 2.dp.toPx()
        drawRoundRect(
            PrimaryButtonColor,
            Offset(1.dp.toPx(), 2.dp.toPx()),
            Size(13.dp.toPx(), 24.dp.toPx()),
            androidx.compose.ui.geometry.CornerRadius(3.dp.toPx()),
        )
        drawRoundRect(
            PrimaryButtonColor,
            Offset(21.dp.toPx(), 2.dp.toPx()),
            Size(13.dp.toPx(), 24.dp.toPx()),
            androidx.compose.ui.geometry.CornerRadius(3.dp.toPx()),
        )
        drawCircle(CardBgColor, 2.2.dp.toPx(), Offset(7.5.dp.toPx(), 8.dp.toPx()))
        drawCircle(CardBgColor, 2.2.dp.toPx(), Offset(27.5.dp.toPx(), 8.dp.toPx()))
        drawLine(CardBgColor, Offset(4.dp.toPx(), 14.dp.toPx()), Offset(11.dp.toPx(), 14.dp.toPx()), stroke, StrokeCap.Round)
        drawLine(CardBgColor, Offset(24.dp.toPx(), 14.dp.toPx()), Offset(31.dp.toPx(), 14.dp.toPx()), stroke, StrokeCap.Round)
        drawLine(CardBgColor, Offset(14.dp.toPx(), 12.dp.toPx()), Offset(21.dp.toPx(), 12.dp.toPx()), stroke, StrokeCap.Round)
    }
}

private enum class NavIcon { GRID, CHAT, PERSON }

@Composable
private fun BottomNavigation(
    selected: MainDestination,
    onCatalog: () -> Unit,
    onProfile: () -> Unit,
) {
    Row(
        Modifier.fillMaxWidth().height(76.dp).padding(horizontal = 22.dp),
        horizontalArrangement = Arrangement.SpaceBetween,
        verticalAlignment = Alignment.CenterVertically,
    ) {
        BottomNavItem("Каталог", NavIcon.GRID, selected == MainDestination.CATALOG, onCatalog)
        BottomNavItem("Мэтчи", NavIcon.CHAT, false) { }
        BottomNavItem("Профиль", NavIcon.PERSON, selected == MainDestination.PROFILE, onProfile)
    }
}

@Composable
private fun BottomNavItem(label: String, icon: NavIcon, selected: Boolean, onClick: () -> Unit) {
    val color = if (selected) CardBgColor else MutedTextColor
    Column(
        Modifier.clickable(onClick = onClick).padding(horizontal = 14.dp, vertical = 6.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
    ) {
        Canvas(Modifier.size(25.dp)) {
            val width = 2.dp.toPx()
            when (icon) {
                NavIcon.GRID -> {
                    val cell = 7.dp.toPx()
                    listOf(
                        Offset(3.dp.toPx(), 3.dp.toPx()), Offset(15.dp.toPx(), 3.dp.toPx()),
                        Offset(3.dp.toPx(), 15.dp.toPx()), Offset(15.dp.toPx(), 15.dp.toPx()),
                    ).forEach {
                        drawRoundRect(color, it, Size(cell, cell), style = Stroke(width))
                    }
                }
                NavIcon.CHAT -> {
                    drawRoundRect(color, Offset(3.dp.toPx(), 3.dp.toPx()), Size(19.dp.toPx(), 15.dp.toPx()), style = Stroke(width))
                    drawLine(color, Offset(7.dp.toPx(), 18.dp.toPx()), Offset(4.dp.toPx(), 22.dp.toPx()), width, StrokeCap.Round)
                }
                NavIcon.PERSON -> {
                    drawCircle(color, 4.dp.toPx(), Offset(12.5.dp.toPx(), 7.dp.toPx()), style = Stroke(width))
                    drawArc(color, 180f, 180f, false, Offset(4.dp.toPx(), 11.dp.toPx()), Size(17.dp.toPx(), 18.dp.toPx()), style = Stroke(width))
                }
            }
        }
        Text(label, color = color, fontSize = 11.sp)
    }
}

@Composable
fun PageCard(content: @Composable () -> Unit) {
    Surface(
        modifier = Modifier.fillMaxSize().padding(horizontal = 14.dp),
        color = CardBgColor,
        shape = RoundedCornerShape(26.dp),
        content = content,
    )
}

@Composable
fun PageTitle(text: String) {
    Text(text, color = TextDarkColor, fontSize = 27.sp, fontWeight = FontWeight.Bold, modifier = Modifier.padding(bottom = 6.dp))
}

@Composable
fun StepProgress(progress: Float) {
    Box(Modifier.fillMaxWidth().padding(vertical = 18.dp).height(4.dp).background(SectionBgColor, RoundedCornerShape(2.dp))) {
        Box(Modifier.fillMaxWidth(progress).height(4.dp).background(PrimaryButtonColor, RoundedCornerShape(2.dp)))
    }
}

@Composable
fun FormLabel(text: String) {
    Text(text, color = TextDarkColor, fontSize = 14.sp, fontWeight = FontWeight.Bold, modifier = Modifier.padding(top = 14.dp, bottom = 6.dp))
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun FormField(
    value: String,
    onValueChange: (String) -> Unit,
    placeholder: String,
    minLines: Int = 1,
) {
    OutlinedTextField(
        value = value,
        onValueChange = onValueChange,
        modifier = Modifier.fillMaxWidth(),
        placeholder = { Text(placeholder, color = MutedTextColor) },
        minLines = minLines,
        shape = RoundedCornerShape(13.dp),
        keyboardOptions = KeyboardOptions(imeAction = ImeAction.Next),
        colors = TextFieldDefaults.colors(
            focusedContainerColor = Color(0xFFFFFAEB),
            unfocusedContainerColor = Color(0xFFFFFAEB),
            focusedIndicatorColor = MutedTextColor,
            unfocusedIndicatorColor = Color(0xFFD1AAA0),
            focusedTextColor = TextDarkColor,
            unfocusedTextColor = TextDarkColor,
        ),
    )
}

@Composable
fun SkillChips(skills: List<String>, onRemove: ((String) -> Unit)? = null) {
    Row(horizontalArrangement = Arrangement.spacedBy(8.dp), modifier = Modifier.padding(vertical = 6.dp)) {
        skills.take(4).forEach { skill ->
            Surface(
                color = SectionBgColor,
                shape = RoundedCornerShape(18.dp),
                modifier = if (onRemove == null) Modifier else Modifier.clickable { onRemove(skill) },
            ) {
                Text(
                    if (onRemove == null) skill else "$skill  ×",
                    color = TextDarkColor,
                    fontSize = 14.sp,
                    modifier = Modifier.padding(horizontal = 13.dp, vertical = 7.dp),
                )
            }
        }
    }
}

@Composable
fun ExpandableHeader(title: String, expanded: Boolean, onClick: () -> Unit) {
    Row(
        Modifier.fillMaxWidth().padding(top = 14.dp)
            .background(SectionBgColor, RoundedCornerShape(13.dp))
            .clickable(onClick = onClick).padding(horizontal = 13.dp, vertical = 16.dp),
        horizontalArrangement = Arrangement.SpaceBetween,
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Text(title, color = TextDarkColor, fontWeight = FontWeight.Bold)
        Text(if (expanded) "⌃" else "⌄", color = TextDarkColor, fontSize = 24.sp)
    }
}

@Composable
fun PrimaryButton(text: String, onClick: () -> Unit, enabled: Boolean = true) {
    Button(
        onClick = onClick,
        enabled = enabled,
        modifier = Modifier.fillMaxWidth().height(52.dp),
        shape = RoundedCornerShape(13.dp),
        colors = ButtonDefaults.buttonColors(
            containerColor = PrimaryButtonColor,
            disabledContainerColor = DisabledButtonColor,
        ),
    ) {
        Text(text, color = CardBgColor, fontSize = 16.sp, fontWeight = FontWeight.Bold)
    }
}

fun initials(name: String): String = name
    .split(" ")
    .filter { it.isNotBlank() }
    .take(2)
    .joinToString("") { it.first().uppercase() }
    .ifBlank { "П" }
