#define UNICODE
#define _UNICODE
#include <windows.h>
#include <gdiplus.h>
#include <mmsystem.h>
#include <vector>
#include <string>
#include <sstream>
#include <iomanip>
#include <cmath>
#include <algorithm>
#include "GameData.hpp"

using namespace Gdiplus;

// --- ГЛОБАЛЬНЫЕ КОНСТАНТЫ И ПЕРЕМЕННЫЕ ---
const int WINDOW_WIDTH = 1200;
const int WINDOW_HEIGHT = 800;

enum TabIndex {
    TAB_OFFICE = 0,
    TAB_DEV_WIZARD = 1,
    TAB_PORTFOLIO = 2,
    TAB_STAFF = 3,
    TAB_ENGINES = 4,
    TAB_RESEARCH = 5,
    TAB_UPGRADES = 6,
    TAB_ACHIEVEMENTS = 7
};

TabIndex currentTab = TAB_OFFICE;

// Экономика и статистика
long long g_money = 25000;
long long g_fans = 25;
int g_rp = 20;
double g_stockPrice = 50.0;
double g_stockGrowth = 0.0;
int g_morale = 100;
int g_year = 1;
int g_month = 1;
int g_week = 1;
int g_speed = 1; // 0 = pause, 1 = 1x, 2 = 2x, 5 = 5x

int g_currentOfficeIdx = 0;

// Данные игры
std::vector<Genre> g_genres;
std::vector<Theme> g_themes;
std::vector<Platform> g_platforms;
std::vector<CustomEngine> g_engines;
std::vector<Office> g_offices;
std::vector<Employee> g_staff;
std::vector<ReleasedGame> g_games;
std::vector<Achievement> g_achievements;
std::vector<std::string> g_unlockedTech;
std::vector<std::wstring> g_feedLogs;
std::vector<BugTarget> g_huntBugs;

// Текущая разработка
bool g_isDevActive = false;
std::wstring g_devTitle = L"Cyber Odyssey";
int g_devGenreIdx = 0;
int g_devThemeIdx = 0;
int g_devPlatformIdx = 0;
int g_devEngineIdx = 0;
int g_devScale = 0; // 0: Indie, 1: AA, 2: AAA
int g_devMonetization = 0; // 0: Premium, 1: F2P, 2: MMO
int g_sliderGameplay = 40;
int g_sliderGraphics = 30;
int g_sliderSound = 30;
double g_devProgress = 0.0;
int g_devPtsCode = 0;
int g_devPtsDesign = 0;
int g_devPtsSound = 0;
int g_devPtsBugs = 0;
bool g_isCrunch = false;

// Окно ревью (после завершения)
bool g_showReviewDialog = false;
ReleasedGame g_lastReviewedGame;
std::vector<std::pair<std::wstring, double>> g_lastReviewScores;

// Окно Охоты на баги
bool g_showBugHuntDialog = false;
int g_bugHuntTimer = 10;
int g_bugsSquashed = 0;

// Вспомогательный генератор
void InitDatabase() {
    g_genres = {
        {"rpg", L"RPG (Ролевая игра)", 2000, 0, {"fantasy", "scifi", "postapoc"}, 40, 35, 25},
        {"action", L"Экшен / Шутер", 2500, 0, {"scifi", "military", "cyberpunk"}, 45, 35, 20},
        {"strategy", L"Стратегия в реальном времени", 2800, 20, {"history", "space", "medieval"}, 50, 30, 20},
        {"sim", L"Симулятор жизни / бизнеса", 1500, 0, {"business", "city"}, 45, 30, 25},
        {"horror", L"Хоррор на выживание", 2200, 25, {"zombie", "mystery"}, 30, 35, 35},
        {"puzzle", L"Головоломка / Казуалка", 1000, 15, {"abstract", "fantasy"}, 35, 45, 20}
    };

    g_themes = {
        {"fantasy", L"Фэнтези и Магия", 0},
        {"scifi", L"Научная фантастика", 0},
        {"cyberpunk", L"Киберпанк 2099", 20},
        {"postapoc", L"Постапокалипсис", 25},
        {"zombie", L"Зомби-эпидемия", 15},
        {"space", L"Космическая одиссея", 20},
        {"medieval", L"Средневековье", 0},
        {"business", L"Бизнес и корпорации", 15}
    };

    g_platforms = {
        {"pc", L"ПК / Steam", 1000, 1.0, 0},
        {"playbox", L"PlayBox 5 Console", 4500, 1.35, 30},
        {"switchy", L"Switchy OLED", 3000, 1.15, 25},
        {"mobile", L"Мобильные телефоны", 2500, 1.55, 20},
        {"vr", L"Шлем VR Neo", 7000, 0.9, 45}
    };

    g_engines = {
        {"basic", L"Базовый 2D движок v1.0", 1.0, {L"2D Спрайты"}, false},
        {"vortex", L"Vortex 3D Engine (Custom)", 1.45, {L"3D Физика", L"ИИ врагов"}, true}
    };

    g_offices = {
        {"garage", L"Гараж родителей", 2, 0, 0, L"Тесный гараж. Хватит на двух энтузиастов."},
        {"coworking", L"Коворкинг в центре", 4, 1500, 15000, L"Современный офис с быстрым интернетом и кофе."},
        {"studio", L"Собственная студия разработки", 6, 4500, 50000, L"Просторный офис со звукозаписью и переговорками."},
        {"skyscraper", L"Небоскрёб GameDev Corp", 8, 12000, 200000, L"Легендарная штаб-квартира мирового титана индустрии!"}
    };

    g_staff = {
        {1, L"Вы (Основатель)", L"Главный Геймдизайнер", 20, 18, 15, 0, 100},
        {2, L"Максим Орлов", L"Senior Программист", 28, 10, 8, 1200, 100}
    };

    g_achievements = {
        {"first_game", L"Первый шаг", L"Выпустите свою первую игру", 3000, 10, false},
        {"hit", L"Признание прессы", L"Получите средний балл 8.0+", 8000, 20, false},
        {"masterpiece", L"Шедевр года", L"Получите оценку 9.5+", 25000, 35, false},
        {"millionaire", L"Миллионер", L"Заработайте $1,000,000 выручки", 50000, 50, false}
    };

    g_feedLogs.push_back(L"Добро пожаловать в GameDev Studio Tycoon Pro (C++ Native)!");
}

// Звуковые сигналы через Windows API
void PlaySoundBeep(int freq, int duration) {
    Beep(freq, duration);
}

void CheckAchievements() {
    for (auto& a : g_achievements) {
        if (a.unlocked) continue;
        bool sat = false;
        if (a.id == "first_game" && g_games.size() >= 1) sat = true;
        if (a.id == "hit" && std::any_of(g_games.begin(), g_games.end(), [](const ReleasedGame& g){ return g.score >= 8.0; })) sat = true;
        if (a.id == "masterpiece" && std::any_of(g_games.begin(), g_games.end(), [](const ReleasedGame& g){ return g.score >= 9.5; })) sat = true;
        if (a.id == "millionaire") {
            long long total = 0;
            for (auto& g : g_games) total += g.revenue;
            if (total >= 1000000) sat = true;
        }

        if (sat) {
            a.unlocked = true;
            g_money += a.rewardCash;
            g_rp += a.rewardRp;
            g_feedLogs.insert(g_feedLogs.begin(), L"🏆 ДОСТИЖЕНИЕ: " + a.title + L" (+$" + std::to_wstring(a.rewardCash) + L")");
            MessageBeep(MB_ICONASTERISK);
        }
    }
}

void StartDevelopment() {
    if (g_isDevActive) return;

    int cost = g_genres[g_devGenreIdx].cost + g_platforms[g_devPlatformIdx].cost;
    if (g_devScale == 1) cost = (int)(cost * 1.5);
    if (g_devScale == 2) cost = cost * 3;

    if (g_money < cost) {
        MessageBoxW(NULL, L"Недостаточно средств для запуска разработки!", L"Внимание", MB_OK | MB_ICONWARNING);
        return;
    }

    g_money -= cost;
    g_devProgress = 0.0;
    g_devPtsCode = 0;
    g_devPtsDesign = 0;
    g_devPtsSound = 0;
    g_devPtsBugs = 0;
    g_isDevActive = true;

    g_feedLogs.insert(g_feedLogs.begin(), L"Начата разработка: «" + g_devTitle + L"» (" + g_genres[g_devGenreIdx].name + L")");
    currentTab = TAB_OFFICE;
}

void FinishDevelopment() {
    if (!g_isDevActive) return;

    double scoreBase = 7.0;
    bool isSynergy = false;
    for (const auto& t : g_genres[g_devGenreIdx].bestThemes) {
        if (t == g_themes[g_devThemeIdx].id) { isSynergy = true; break; }
    }
    if (isSynergy) scoreBase = 9.0;

    double bugPenalty = g_devPtsBugs * 0.3;
    double rawScore = scoreBase - bugPenalty + ((rand() % 16 - 8) / 10.0);
    if (rawScore > 10.0) rawScore = 10.0;
    if (rawScore < 2.0) rawScore = 2.0;
    double finalScore = std::round(rawScore * 10.0) / 10.0;

    int price = 20;
    if (g_devMonetization == 1) price = 0; // F2P
    if (g_devMonetization == 2) price = 10; // MMO

    ReleasedGame game;
    game.id = (long long)GetTickCount64();
    game.title = g_devTitle;
    game.genre = g_genres[g_devGenreIdx].name;
    game.theme = g_themes[g_devThemeIdx].name;
    game.platform = g_platforms[g_devPlatformIdx].name;
    game.engine = g_engines[g_devEngineIdx].name;
    game.monetization = (g_devMonetization == 1 ? "f2p" : (g_devMonetization == 2 ? "mmo" : "premium"));
    game.score = finalScore;
    game.copiesSold = 0;
    game.revenue = 0;
    game.weeksOnMarket = 0;
    game.price = price;
    game.marketingMultiplier = 1.2;
    game.dlcCount = 0;
    game.audiencePool = (long long)(25000 * g_platforms[g_devPlatformIdx].audienceShare * std::pow(finalScore / 4.0, 3));

    g_games.insert(g_games.begin(), game);
    g_lastReviewedGame = game;

    g_lastReviewScores.clear();
    g_lastReviewScores.push_back({L"Игромания", std::min(10.0, std::max(1.0, finalScore + (rand()%7 - 3)/10.0))});
    g_lastReviewScores.push_back({L"GameSpot", std::min(10.0, std::max(1.0, finalScore + (rand()%7 - 3)/10.0))});
    g_lastReviewScores.push_back({L"PC Gamer", std::min(10.0, std::max(1.0, finalScore + (rand()%7 - 3)/10.0))});
    g_lastReviewScores.push_back({L"IGN Global", std::min(10.0, std::max(1.0, finalScore + (rand()%7 - 3)/10.0))});

    int fansGain = (int)(std::pow(finalScore, 2.5) * 12 + g_fans * 0.1);
    g_fans += fansGain;
    g_rp += (int)(finalScore * 3.5);

    g_isDevActive = false;
    g_showReviewDialog = true;
    MessageBeep(MB_OK);

    CheckAchievements();
}

void StartBugHunt() {
    if (!g_isDevActive || g_devPtsBugs <= 0) return;
    g_showBugHuntDialog = true;
    g_bugHuntTimer = 10;
    g_bugsSquashed = 0;
    g_huntBugs.clear();

    for (int i = 0; i < std::min(12, std::max(4, g_devPtsBugs)); i++) {
        BugTarget b;
        b.x = (float)(100 + rand() % 500);
        b.y = (float)(100 + rand() % 300);
        b.size = 35.0f;
        b.alive = true;
        g_huntBugs.push_back(b);
    }
}

void TickWeek() {
    g_week++;
    if (g_week > 4) {
        g_week = 1;
        g_month++;
        // Месячные расходы
        int rent = g_offices[g_currentOfficeIdx].rent;
        int sal = 0;
        for (const auto& emp : g_staff) sal += emp.salary;
        g_money -= (rent + sal);

        // Отчисления за движки
        for (const auto& eng : g_engines) {
            if (eng.isProprietary) {
                g_money += (int)(eng.mult * 900);
            }
        }
    }
    if (g_month > 12) {
        g_month = 1;
        g_year++;
        g_feedLogs.insert(g_feedLogs.begin(), L"🎉 Наступил " + std::to_wstring(g_year) + L"-й год работы студии!");
    }

    // Прогресс разработки
    if (g_isDevActive) {
        int tCode = 0, tDesign = 0, tSound = 0;
        for (const auto& s : g_staff) {
            tCode += s.code; tDesign += s.design; tSound += s.sound;
        }

        double mult = g_engines[g_devEngineIdx].mult;
        if (g_isCrunch) { mult *= 1.8; g_morale = std::max(10, g_morale - 1); }

        g_devPtsCode += std::max(1, (int)(tCode * (g_sliderGameplay / 40.0) * mult / 5.0));
        g_devPtsDesign += std::max(1, (int)(tDesign * (g_sliderGraphics / 30.0) * mult / 5.0));
        g_devPtsSound += std::max(1, (int)(tSound * (g_sliderSound / 30.0) * mult / 5.0));

        if (rand() % 100 < (g_isCrunch ? 55 : 30)) {
            g_devPtsBugs += (rand() % 2 + 1);
        }

        if (rand() % 100 < 25) g_rp++;

        double step = (tCode + tDesign + tSound) / (g_devScale == 2 ? 70.0 : (g_devScale == 1 ? 50.0 : 35.0));
        g_devProgress += step * (g_isCrunch ? 1.6 : 1.0);
        if (g_devProgress >= 100.0) {
            g_devProgress = 100.0;
        }
    }

    // Продажи игр
    for (auto& game : g_games) {
        if (game.weeksOnMarket > 28) continue;
        game.weeksOnMarket++;
        double decay = std::pow(0.88, game.weeksOnMarket);

        long long sold = 0;
        long long inc = 0;
        if (game.monetization == "f2p") {
            sold = (long long)(game.audiencePool * 0.3 * decay + g_fans * 0.15 * decay);
            inc = (long long)(sold * (2.5 + game.score * 0.5));
        } else {
            sold = (long long)(game.audiencePool * 0.14 * decay + g_fans * 0.05 * decay);
            inc = sold * game.price;
        }

        if (sold > 0) {
            game.copiesSold += sold;
            game.revenue += inc;
            g_money += inc;
        }
    }

    // Акции
    double delta = ((rand() % 20 - 9) / 10.0);
    if (g_money > 100000) delta += 1.0;
    if (g_money < 0) delta -= 2.0;
    g_stockPrice = std::max(5.0, g_stockPrice + delta);
    g_stockGrowth = delta;

    CheckAchievements();
}

// --- ОТРИСОВКА ИНТЕРФЕЙСА (GDI+) ---
void DrawGame(HDC hdc, RECT rc) {
    Graphics g(hdc);
    g.SetSmoothingMode(SmoothingModeAntiAlias);
    g.SetTextRenderingHint(TextRenderingHintClearTypeGridFit);

    // Задний фон окна
    SolidBrush bgDark(Color(255, 11, 13, 20));
    g.FillRectangle(&bgDark, 0, 0, rc.right, rc.bottom);

    // ВЕРХНЯЯ ПАНЕЛЬ СТАТИСТИКИ
    SolidBrush topNavBg(Color(255, 21, 24, 36));
    g.FillRectangle(&topNavBg, 0, 0, rc.right, 70);
    Pen borderPen(Color(255, 39, 44, 66), 1.0f);
    g.DrawLine(&borderPen, 0, 70, rc.right, 70);

    FontFamily fontFamily(L"Segoe UI");
    Font fontTitle(&fontFamily, 14, FontStyleBold, UnitPixel);
    Font fontSub(&fontFamily, 11, FontStyleRegular, UnitPixel);
    Font fontBody(&fontFamily, 12, FontStyleRegular, UnitPixel);
    Font fontBold(&fontFamily, 12, FontStyleBold, UnitPixel);
    Font fontBig(&fontFamily, 22, FontStyleBold, UnitPixel);

    SolidBrush textWhite(Color(255, 243, 244, 246));
    SolidBrush textMuted(Color(255, 156, 163, 175));
    SolidBrush accentGold(Color(255, 245, 158, 11));
    SolidBrush accentGreen(Color(255, 16, 185, 129));
    SolidBrush accentCyan(Color(255, 6, 182, 212));
    SolidBrush accentPurple(Color(255, 139, 92, 246));
    SolidBrush accentRed(Color(255, 239, 68, 68));

    // Название студии
    g.DrawString(L"🎮 Pixel Forge Studios (C++ Native)", -1, &fontTitle, PointF(20, 16), &textWhite);
    std::wstring tierStr = g_offices[g_currentOfficeIdx].name + L" (Офис ур. " + std::to_wstring(g_currentOfficeIdx + 1) + L")";
    g.DrawString(tierStr.c_str(), -1, &fontSub, PointF(20, 38), &accentPurple);

    // Статистика справа
    std::wstringstream ssMoney;
    ssMoney << L"$" << g_money;
    g.DrawString(ssMoney.str().c_str(), -1, &fontTitle, PointF(420, 16), g_money < 0 ? &accentRed : &accentGold);
    g.DrawString(L"Баланс студии", -1, &fontSub, PointF(420, 38), &textMuted);

    std::wstringstream ssFans;
    ssFans << g_fans << L" фан.";
    g.DrawString(ssFans.str().c_str(), -1, &fontTitle, PointF(570, 16), &accentRed);
    g.DrawString(L"Популярность", -1, &fontSub, PointF(570, 38), &textMuted);

    std::wstringstream ssRp;
    ssRp << g_rp << L" RP";
    g.DrawString(ssRp.str().c_str(), -1, &fontTitle, PointF(700, 16), &accentCyan);
    g.DrawString(L"Очки исследований", -1, &fontSub, PointF(700, 38), &textMuted);

    std::wstringstream ssStock;
    ssStock << std::fixed << std::setprecision(2) << L"$" << g_stockPrice;
    g.DrawString(ssStock.str().c_str(), -1, &fontTitle, PointF(830, 16), &accentPurple);
    g.DrawString(L"Акции студии", -1, &fontSub, PointF(830, 38), &textMuted);

    std::wstringstream ssDate;
    ssDate << L"Год " << g_year << L", Мес " << g_month << L", Нед " << g_week;
    g.DrawString(ssDate.str().c_str(), -1, &fontTitle, PointF(960, 16), &textWhite);
    std::wstring spStr = (g_speed == 0 ? L"Пауза [P]" : (g_speed == 1 ? L"Скорость 1x" : (g_speed == 2 ? L"Скорость 2x" : L"Скорость 5x")));
    g.DrawString(spStr.c_str(), -1, &fontSub, PointF(960, 38), &accentGreen);

    // БОКОВОЕ МЕНЮ (САЙДБАР)
    SolidBrush sideBg(Color(255, 21, 24, 36));
    g.FillRectangle(&sideBg, 0, 70, 220, rc.bottom - 70);
    g.DrawLine(&borderPen, 220, 70, 220, rc.bottom);

    const wchar_t* tabs[] = {
        L"🏢 Офис студии",
        L"🚀 Новая игра",
        L"🏆 Выпущенные игры",
        L"👥 Персонал",
        L"⚙️ Конструктор Движков",
        L"🔬 Исследования",
        L"📈 Улучшения офиса",
        L"🎯 Достижения"
    };

    SolidBrush btnActiveBg(Color(255, 99, 102, 241));
    SolidBrush btnHoverBg(Color(255, 30, 35, 52));

    for (int i = 0; i < 8; i++) {
        int y = 90 + i * 44;
        if (currentTab == (TabIndex)i) {
            g.FillRectangle(&btnActiveBg, 12, y, 196, 36);
            g.DrawString(tabs[i], -1, &fontBold, PointF(24, y + 8), &textWhite);
        } else {
            g.DrawString(tabs[i], -1, &fontBody, PointF(24, y + 8), &textMuted);
        }
    }

    // Быстрые кнопки внизу сайдбара
    SolidBrush quickDevBtn(Color(255, 79, 70, 229));
    g.FillRectangle(&quickDevBtn, 12, rc.bottom - 110, 196, 40);
    g.DrawString(L"➕ Создать игру [N]", -1, &fontBold, PointF(40, rc.bottom - 98), &textWhite);

    SolidBrush quickContrBtn(Color(255, 32, 37, 56));
    g.FillRectangle(&quickContrBtn, 12, rc.bottom - 60, 196, 38);
    g.DrawString(L"💼 Фриланс +$3,000 [F]", -1, &fontBold, PointF(30, rc.bottom - 48), &accentCyan);

    // ОСНОВНОЙ КОНТЕНТНЫЙ БЛОК
    int cx = 240;
    int cy = 90;

    if (currentTab == TAB_OFFICE) {
        g.DrawString(L"Главный офис разработки", -1, &fontTitle, PointF(cx, cy), &textWhite);
        g.DrawString(L"Следите за прогрессом команды, кликайте баги и выпускайте хиты!", -1, &fontSub, PointF(cx, cy + 24), &textMuted);

        // Интерактивная 2D сцена комнаты офиса
        SolidBrush stageBg(Color(255, 18, 21, 33));
        g.FillRectangle(&stageBg, cx, cy + 50, 920, 320);
        g.DrawRectangle(&borderPen, cx, cy + 50, 920, 320);

        // Столы сотрудников
        int deskW = 190, deskH = 120;
        for (size_t i = 0; i < g_staff.size(); i++) {
            int dx = cx + 30 + (int)(i % 4) * 220;
            int dy = cy + 70 + (int)(i / 4) * 140;

            SolidBrush deskBg(Color(255, 27, 32, 50));
            g.FillRectangle(&deskBg, dx, dy, deskW, deskH);
            g.DrawRectangle(&borderPen, dx, dy, deskW, deskH);

            g.DrawString(L"💻 Рабочее место", -1, &fontSub, PointF(dx + 10, dy + 8), &accentCyan);
            g.DrawString(g_staff[i].name.c_str(), -1, &fontBold, PointF(dx + 10, dy + 28), &textWhite);
            g.DrawString(g_staff[i].role.c_str(), -1, &fontSub, PointF(dx + 10, dy + 48), &accentPurple);

            std::wstringstream ssSt;
            ssSt << L"Код:" << g_staff[i].code << L"  Арт:" << g_staff[i].design << L"  Зв:" << g_staff[i].sound;
            g.DrawString(ssSt.str().c_str(), -1, &fontSub, PointF(dx + 10, dy + 70), &textMuted);

            std::wstring salStr = L"$" + std::to_wstring(g_staff[i].salary) + L"/мес";
            g.DrawString(salStr.c_str(), -1, &fontSub, PointF(dx + 10, dy + 92), &accentGold);
        }

        // Пустые слоты
        for (size_t i = g_staff.size(); i < (size_t)g_offices[g_currentOfficeIdx].capacity; i++) {
            int dx = cx + 30 + (int)(i % 4) * 220;
            int dy = cy + 70 + (int)(i / 4) * 140;
            Pen dashedPen(Color(255, 60, 68, 95), 1.0f);
            dashedPen.SetDashStyle(DashStyleDash);
            g.DrawRectangle(&dashedPen, dx, dy, deskW, deskH);
            g.DrawString(L"🪑 Свободный стол", -1, &fontSub, PointF(dx + 35, dy + 45), &textMuted);
            g.DrawString(L"[Клик в Персонале]", -1, &fontSub, PointF(dx + 30, dy + 65), &accentPurple);
        }

        // Панель текущей разработки (если идет)
        if (g_isDevActive) {
            int devY = cy + 390;
            SolidBrush activeDevBg(Color(255, 23, 27, 43));
            g.FillRectangle(&activeDevBg, cx, devY, 920, 100);
            g.DrawRectangle(&borderPen, cx, devY, 920, 100);

            std::wstring dTitle = L"⏳ Разработка: «" + g_devTitle + L"» (" + g_genres[g_devGenreIdx].name + L")";
            g.DrawString(dTitle.c_str(), -1, &fontBold, PointF(cx + 16, devY + 12), &textWhite);

            std::wstringstream ssPts;
            ssPts << L"Код: " << g_devPtsCode << L"  |  Арт: " << g_devPtsDesign << L"  |  Звук: " << g_devPtsSound << L"  |  Баги: " << g_devPtsBugs;
            g.DrawString(ssPts.str().c_str(), -1, &fontBold, PointF(cx + 420, devY + 12), g_devPtsBugs > 5 ? &accentRed : &accentGreen);

            // Полоса прогресса
            SolidBrush trackBg(Color(255, 14, 16, 26));
            g.FillRectangle(&trackBg, cx + 16, devY + 40, 888, 14);
            int fillW = (int)(888 * (g_devProgress / 100.0));
            SolidBrush fillBg(Color(255, 99, 102, 241));
            g.FillRectangle(&fillBg, cx + 16, devY + 40, fillW, 14);

            // Кнопки управления разработкой
            SolidBrush btnBugHuntBg(Color(255, 220, 38, 38));
            g.FillRectangle(&btnBugHuntBg, cx + 16, devY + 62, 170, 28);
            g.DrawString(L"🎯 Охота на баги [B]", -1, &fontBold, PointF(cx + 26, devY + 68), &textWhite);

            SolidBrush btnCrunchBg(g_isCrunch ? Color(255, 234, 88, 12) : Color(255, 35, 41, 64));
            g.FillRectangle(&btnCrunchBg, cx + 200, devY + 62, 160, 28);
            g.DrawString(L"🔥 Кранч x2 [C]", -1, &fontBold, PointF(cx + 225, devY + 68), &textWhite);

            SolidBrush btnReleaseBg(Color(255, 16, 185, 129));
            g.FillRectangle(&btnReleaseBg, cx + 720, devY + 62, 184, 28);
            g.DrawString(L"🚀 Выпустить игру! [R]", -1, &fontBold, PointF(cx + 740, devY + 68), &textWhite);
        }

        // Лента новостей
        int logY = cy + (g_isDevActive ? 505 : 390);
        g.DrawString(L"Информационная лента:", -1, &fontBold, PointF(cx, logY), &textWhite);
        for (size_t i = 0; i < std::min((size_t)6, g_feedLogs.size()); i++) {
            g.DrawString(g_feedLogs[i].c_str(), -1, &fontSub, PointF(cx + 10, logY + 22 + (int)i * 20), &accentGold);
        }
    }
    else if (currentTab == TAB_DEV_WIZARD) {
        g.DrawString(L"Конструктор новой игры", -1, &fontTitle, PointF(cx, cy), &textWhite);
        g.DrawString(L"Выберите идеальную комбинацию механик и настройте ползунки приоритетов", -1, &fontSub, PointF(cx, cy + 24), &textMuted);

        SolidBrush formBg(Color(255, 21, 24, 36));
        g.FillRectangle(&formBg, cx, cy + 60, 800, 520);
        g.DrawRectangle(&borderPen, cx, cy + 60, 800, 520);

        g.DrawString(L"1. Название проекта: [Кликните или нажмите Tab 1-9 для выбора]", -1, &fontBold, PointF(cx + 30, cy + 80), &textWhite);
        g.DrawString(g_devTitle.c_str(), -1, &fontBig, PointF(cx + 30, cy + 105), &accentGold);

        // Жанры
        g.DrawString(L"2. Жанр игры [Клавиши 1-6]:", -1, &fontBold, PointF(cx + 30, cy + 150), &textWhite);
        for (size_t i = 0; i < g_genres.size(); i++) {
            std::wstringstream ssG;
            ssG << L"[" << (i + 1) << L"] " << g_genres[i].name;
            SolidBrush b((int)i == g_devGenreIdx ? Color(255, 99, 102, 241) : Color(255, 156, 163, 175));
            g.DrawString(ssG.str().c_str(), -1, &fontBold, PointF(cx + 30 + (int)(i % 2) * 360, cy + 175 + (int)(i / 2) * 26), &b);
        }

        // Тематика
        g.DrawString(L"3. Сеттинг / Тематика [Клавиши Q, W, E, R, T, Y]:", -1, &fontBold, PointF(cx + 30, cy + 265), &textWhite);
        const wchar_t* keys[] = {L"[Q] ", L"[W] ", L"[E] ", L"[R] ", L"[T] ", L"[Y] "};
        for (size_t i = 0; i < std::min((size_t)6, g_themes.size()); i++) {
            std::wstring thStr = keys[i] + g_themes[i].name;
            SolidBrush b((int)i == g_devThemeIdx ? Color(255, 16, 185, 129) : Color(255, 156, 163, 175));
            g.DrawString(thStr.c_str(), -1, &fontBold, PointF(cx + 30 + (int)(i % 2) * 360, cy + 290 + (int)(i / 2) * 26), &b);
        }

        // Платформа
        g.DrawString(L"4. Платформа [Клавиши Z, X, C, V]:", -1, &fontBold, PointF(cx + 30, cy + 380), &textWhite);
        const wchar_t* pkeys[] = {L"[Z] ", L"[X] ", L"[C] ", L"[V] "};
        for (size_t i = 0; i < std::min((size_t)4, g_platforms.size()); i++) {
            std::wstring plStr = pkeys[i] + g_platforms[i].name;
            SolidBrush b((int)i == g_devPlatformIdx ? Color(255, 6, 182, 212) : Color(255, 156, 163, 175));
            g.DrawString(plStr.c_str(), -1, &fontBold, PointF(cx + 30 + (int)(i % 2) * 360, cy + 405 + (int)(i / 2) * 26), &b);
        }

        // Кнопка старта
        SolidBrush btnStartDev(Color(255, 99, 102, 241));
        g.FillRectangle(&btnStartDev, cx + 30, cy + 480, 740, 50);
        g.DrawString(L"🚀 НАЧАТЬ РАЗРАБОТКУ [НАЖМИТЕ ENTER]", -1, &fontBig, PointF(cx + 170, cy + 490), &textWhite);
    }
    else if (currentTab == TAB_PORTFOLIO) {
        g.DrawString(L"Портфолио выпущенных видеоигр", -1, &fontTitle, PointF(cx, cy), &textWhite);
        g.DrawString(L"История успехов, тиражи, рецензии прессы и дополнения (DLC)", -1, &fontSub, PointF(cx, cy + 24), &textMuted);

        if (g_games.empty()) {
            g.DrawString(L"Вы пока не выпустили ни одной игры. Нажмите 'Новая игра'!", -1, &fontBold, PointF(cx + 100, cy + 150), &textMuted);
        } else {
            for (size_t i = 0; i < std::min((size_t)5, g_games.size()); i++) {
                int gy = cy + 60 + (int)i * 105;
                SolidBrush cardBg(Color(255, 21, 24, 36));
                g.FillRectangle(&cardBg, cx, gy, 880, 95);
                g.DrawRectangle(&borderPen, cx, gy, 880, 95);

                g.DrawString(g_games[i].title.c_str(), -1, &fontBig, PointF(cx + 20, gy + 12), &textWhite);

                std::wstringstream ssTags;
                ssTags << g_games[i].genre << L"  |  " << g_games[i].theme << L"  |  " << g_games[i].platform << L"  |  " << g_games[i].engine;
                g.DrawString(ssTags.str().c_str(), -1, &fontSub, PointF(cx + 20, gy + 42), &accentPurple);

                std::wstringstream ssSales;
                ssSales << L"Продано: " << g_games[i].copiesSold << L" шт.   Выручка: +$" << g_games[i].revenue;
                g.DrawString(ssSales.str().c_str(), -1, &fontBold, PointF(cx + 20, gy + 66), &accentGreen);

                // Оценка
                std::wstringstream ssSc;
                ssSc << std::fixed << std::setprecision(1) << g_games[i].score;
                SolidBrush scoreBg(Color(255, 30, 35, 52));
                g.FillRectangle(&scoreBg, cx + 780, gy + 15, 75, 65);
                g.DrawString(ssSc.str().c_str(), -1, &fontBig, PointF(cx + 795, gy + 30), g_games[i].score >= 8.0 ? &accentGold : &accentCyan);
            }
        }
    }
    else if (currentTab == TAB_STAFF) {
        g.DrawString(L"Персонал студии и агентство найма", -1, &fontTitle, PointF(cx, cy), &textWhite);
        g.DrawString(L"Нанимайте специалистов, обучайте их и следите за моралью", -1, &fontSub, PointF(cx, cy + 24), &textMuted);

        for (size_t i = 0; i < g_staff.size(); i++) {
            int sy = cy + 60 + (int)i * 100;
            SolidBrush sBg(Color(255, 21, 24, 36));
            g.FillRectangle(&sBg, cx, sy, 880, 90);
            g.DrawRectangle(&borderPen, cx, sy, 880, 90);

            g.DrawString(g_staff[i].name.c_str(), -1, &fontTitle, PointF(cx + 20, sy + 15), &textWhite);
            g.DrawString(g_staff[i].role.c_str(), -1, &fontSub, PointF(cx + 20, sy + 38), &accentPurple);

            std::wstringstream ssSk;
            ssSk << L"Кодинг: " << g_staff[i].code << L"  |  Арт: " << g_staff[i].design << L"  |  Звук: " << g_staff[i].sound;
            g.DrawString(ssSk.str().c_str(), -1, &fontBold, PointF(cx + 20, sy + 60), &accentCyan);

            SolidBrush btnTrainBg(Color(255, 35, 42, 65));
            g.FillRectangle(&btnTrainBg, cx + 720, sy + 25, 130, 38);
            g.DrawString(L"🎓 Обучить [T]", -1, &fontBold, PointF(cx + 735, sy + 36), &textWhite);
        }
    }
    else if (currentTab == TAB_ENGINES) {
        g.DrawString(L"Конструктор Проприетарных Игровых Движков", -1, &fontTitle, PointF(cx, cy), &textWhite);
        g.DrawString(L"Собственные технологии повышают качество игр и приносят роялти", -1, &fontSub, PointF(cx, cy + 24), &textMuted);

        for (size_t i = 0; i < g_engines.size(); i++) {
            int ey = cy + 60 + (int)i * 120;
            SolidBrush eBg(Color(255, 21, 24, 36));
            g.FillRectangle(&eBg, cx, ey, 880, 105);
            g.DrawRectangle(&borderPen, cx, ey, 880, 105);

            g.DrawString(g_engines[i].name.c_str(), -1, &fontTitle, PointF(cx + 20, ey + 15), &textWhite);

            std::wstringstream ssMult;
            ssMult << L"Множитель очков качества: x" << std::fixed << std::setprecision(2) << g_engines[i].mult;
            g.DrawString(ssMult.str().c_str(), -1, &fontBold, PointF(cx + 20, ey + 42), &accentGreen);

            std::wstring modStr = L"Модули: ";
            for (const auto& m : g_engines[i].modules) modStr += m + L", ";
            g.DrawString(modStr.c_str(), -1, &fontSub, PointF(cx + 20, ey + 68), &textMuted);

            if (g_engines[i].isProprietary) {
                g.DrawString(L"Лицензируется сторонними студиями (+$1,300/мес)", -1, &fontSub, PointF(cx + 420, ey + 42), &accentGold);
            }
        }

        SolidBrush btnBuildEng(Color(255, 79, 70, 229));
        g.FillRectangle(&btnBuildEng, cx, cy + 320, 360, 46);
        g.DrawString(L"⚙️ Собрать Titan NextGen Engine ($15,000) [E]", -1, &fontBold, PointF(cx + 15, cy + 334), &textWhite);
    }
    else if (currentTab == TAB_RESEARCH) {
        g.DrawString(L"Лаборатория исследований и патентов (RP Tree)", -1, &fontTitle, PointF(cx, cy), &textWhite);
        g.DrawString(L"Открывайте новые сеттинги, некстген платформы и шейдеры", -1, &fontSub, PointF(cx, cy + 24), &textMuted);

        std::wstringstream ssRpBal;
        ssRpBal << L"Доступный баланс RP: " << g_rp << L" очков";
        g.DrawString(ssRpBal.str().c_str(), -1, &fontBig, PointF(cx, cy + 60), &accentCyan);

        g.DrawString(L"• VR Шлем виртуальной реальности (Стоимость: 45 RP) [Нажмите 7]", -1, &fontBold, PointF(cx, cy + 120), &textWhite);
        g.DrawString(L"• Трассировка лучей RayTracing v2 (Стоимость: 30 RP) [Нажмите 8]", -1, &fontBold, PointF(cx, cy + 160), &textWhite);
        g.DrawString(L"• Симфонический оркестровый синтезатор (Стоимость: 20 RP) [Нажмите 9]", -1, &fontBold, PointF(cx, cy + 200), &textWhite);
    }
    else if (currentTab == TAB_UPGRADES) {
        g.DrawString(L"Улучшения студии и недвижимость", -1, &fontTitle, PointF(cx, cy), &textWhite);
        g.DrawString(L"Переезжайте в большие офисы для расширения команды", -1, &fontSub, PointF(cx, cy + 24), &textMuted);

        for (size_t i = 0; i < g_offices.size(); i++) {
            int oy = cy + 60 + (int)i * 110;
            SolidBrush oBg(Color(255, 21, 24, 36));
            g.FillRectangle(&oBg, cx, oy, 880, 95);
            g.DrawRectangle(&borderPen, cx, oy, 880, 95);

            g.DrawString(g_offices[i].name.c_str(), -1, &fontTitle, PointF(cx + 20, oy + 12), &textWhite);
            g.DrawString(g_offices[i].desc.c_str(), -1, &fontSub, PointF(cx + 20, oy + 36), &textMuted);

            std::wstringstream ssInf;
            ssInf << L"Вместимость: до " << g_offices[i].capacity << L" чел.   Аренда: $" << g_offices[i].rent << L"/мес";
            g.DrawString(ssInf.str().c_str(), -1, &fontBold, PointF(cx + 20, oy + 62), &accentCyan);

            if ((int)i == g_currentOfficeIdx) {
                g.DrawString(L"ТЕКУЩИЙ ОФИС", -1, &fontBold, PointF(cx + 720, oy + 35), &accentGreen);
            } else if ((int)i == g_currentOfficeIdx + 1) {
                SolidBrush bBuy(Color(255, 99, 102, 241));
                g.FillRectangle(&bBuy, cx + 700, oy + 26, 150, 40);
                std::wstring prStr = L"Купить $" + std::to_wstring(g_offices[i].price);
                g.DrawString(prStr.c_str(), -1, &fontBold, PointF(cx + 715, oy + 38), &textWhite);
            }
        }
    }
    else if (currentTab == TAB_ACHIEVEMENTS) {
        g.DrawString(L"Достижения студии", -1, &fontTitle, PointF(cx, cy), &textWhite);
        g.DrawString(L"Выполняйте испытания для получения солидных премий и RP", -1, &fontSub, PointF(cx, cy + 24), &textMuted);

        for (size_t i = 0; i < g_achievements.size(); i++) {
            int ay = cy + 60 + (int)i * 90;
            SolidBrush aBg(Color(255, 21, 24, 36));
            g.FillRectangle(&aBg, cx, ay, 880, 75);
            g.DrawRectangle(&borderPen, cx, ay, 880, 75);

            g.DrawString(g_achievements[i].title.c_str(), -1, &fontTitle, PointF(cx + 20, ay + 12), g_achievements[i].unlocked ? &accentGold : &textWhite);
            g.DrawString(g_achievements[i].desc.c_str(), -1, &fontSub, PointF(cx + 20, ay + 38), &textMuted);

            std::wstringstream ssR;
            ssR << L"Награда: +$" << g_achievements[i].rewardCash << L"  |  +" << g_achievements[i].rewardRp << L" RP";
            g.DrawString(ssR.str().c_str(), -1, &fontBold, PointF(cx + 460, ay + 26), &accentGreen);

            g.DrawString(g_achievements[i].unlocked ? L"ВЫПОЛНЕНО 🏆" : L"ЗАБЛОКИРОВАНО 🔒", -1, &fontBold, PointF(cx + 710, ay + 26), g_achievements[i].unlocked ? &accentGold : &textMuted);
        }
    }

    // МОДАЛЬНОЕ ОКНО РЕЦЕНЗИЙ ПРЕССЫ
    if (g_showReviewDialog) {
        SolidBrush modalBackdrop(Color(200, 0, 0, 0));
        g.FillRectangle(&modalBackdrop, 0, 0, rc.right, rc.bottom);

        SolidBrush modalCard(Color(255, 24, 27, 41));
        g.FillRectangle(&modalCard, 300, 160, 600, 480);
        Pen mPen(Color(255, 99, 102, 241), 2.0f);
        g.DrawRectangle(&mPen, 300, 160, 600, 480);

        g.DrawString(L"ПРЕССА О ВАШЕМ РЕЛИЗЕ!", -1, &fontBig, PointF(410, 190), &accentGold);
        g.DrawString(g_lastReviewedGame.title.c_str(), -1, &fontTitle, PointF(450, 230), &textWhite);

        std::wstringstream ssFinal;
        ssFinal << std::fixed << std::setprecision(1) << g_lastReviewedGame.score;
        Font fontHuge(&fontFamily, 44, FontStyleBold, UnitPixel);
        g.DrawString(ssFinal.str().c_str(), -1, &fontHuge, PointF(550, 270), &accentGold);

        for (size_t i = 0; i < g_lastReviewScores.size(); i++) {
            int ry = 360 + (int)i * 42;
            g.DrawString(g_lastReviewScores[i].first.c_str(), -1, &fontBold, PointF(350, ry), &textWhite);
            std::wstringstream ssS;
            ssS << std::fixed << std::setprecision(1) << g_lastReviewScores[i].second << L" / 10.0";
            g.DrawString(ssS.str().c_str(), -1, &fontBold, PointF(740, ry), &accentGreen);
        }

        SolidBrush btnOk(Color(255, 99, 102, 241));
        g.FillRectangle(&btnOk, 470, 560, 260, 48);
        g.DrawString(L"НАЧАТЬ ПРОДАЖИ! [ENTER]", -1, &fontBold, PointF(505, 574), &textWhite);
    }

    // МОДАЛЬНОЕ ОКНО ОХОТЫ НА БАГИ
    if (g_showBugHuntDialog) {
        SolidBrush modalBackdrop(Color(220, 0, 0, 0));
        g.FillRectangle(&modalBackdrop, 0, 0, rc.right, rc.bottom);

        SolidBrush modalArena(Color(255, 17, 20, 34));
        g.FillRectangle(&modalArena, 250, 140, 700, 500);
        Pen aPen(Color(255, 239, 68, 68), 2.0f);
        g.DrawRectangle(&aPen, 250, 140, 700, 500);

        g.DrawString(L"🎯 ОХОТА НА БАГИ! КЛИКАЙТЕ ПО ЖУКАМ!", -1, &fontBig, PointF(340, 160), &accentRed);
        std::wstringstream ssTimer;
        ssTimer << L"Осталось времени: " << g_bugHuntTimer << L" сек  |  Уничтожено: " << g_bugsSquashed;
        g.DrawString(ssTimer.str().c_str(), -1, &fontTitle, PointF(410, 200), &textWhite);

        // Рисуем жуков
        SolidBrush bugBrush(Color(255, 239, 68, 68));
        for (const auto& b : g_huntBugs) {
            if (b.alive) {
                g.FillEllipse(&bugBrush, (INT)(250 + b.x), (INT)(220 + b.y), (INT)b.size, (INT)b.size);
                g.DrawString(L"🐛", -1, &fontTitle, PointF(250 + b.x + 4, 220 + b.y + 4), &textWhite);
            }
        }

        SolidBrush btnDone(Color(255, 35, 41, 64));
        g.FillRectangle(&btnDone, 480, 580, 240, 42);
        g.DrawString(L"ЗАВЕРШИТЬ ОХОТУ [ESC]", -1, &fontBold, PointF(515, 592), &textWhite);
    }
}

// Обработка кликов мыши
void HandleMouseClick(int x, int y, HWND hwnd) {
    if (g_showReviewDialog) {
        if (x >= 470 && x <= 730 && y >= 560 && y <= 608) {
            g_showReviewDialog = false;
            currentTab = TAB_PORTFOLIO;
            InvalidateRect(hwnd, NULL, FALSE);
        }
        return;
    }

    if (g_showBugHuntDialog) {
        // Проверяем клик по жукам
        for (auto& b : g_huntBugs) {
            if (b.alive) {
                float bx = 250 + b.x;
                float by = 220 + b.y;
                if (x >= bx && x <= bx + b.size && y >= by && y <= by + b.size) {
                    b.alive = false;
                    g_bugsSquashed++;
                    g_devPtsBugs = std::max(0, g_devPtsBugs - 1);
                    PlaySoundBeep(900, 40);
                    InvalidateRect(hwnd, NULL, FALSE);
                    return;
                }
            }
        }
        if (x >= 480 && x <= 720 && y >= 580 && y <= 622) {
            g_showBugHuntDialog = false;
            InvalidateRect(hwnd, NULL, FALSE);
        }
        return;
    }

    // Сайдбар меню
    if (x >= 12 && x <= 208 && y >= 90 && y <= 90 + 8 * 44) {
        int idx = (y - 90) / 44;
        if (idx >= 0 && idx < 8) {
            currentTab = (TabIndex)idx;
            PlaySoundBeep(600, 30);
            InvalidateRect(hwnd, NULL, FALSE);
        }
        return;
    }

    // Быстрый дев
    if (x >= 12 && x <= 208 && y >= WINDOW_HEIGHT - 110 && y <= WINDOW_HEIGHT - 70) {
        currentTab = TAB_DEV_WIZARD;
        PlaySoundBeep(700, 30);
        InvalidateRect(hwnd, NULL, FALSE);
        return;
    }

    // Быстрый фриланс
    if (x >= 12 && x <= 208 && y >= WINDOW_HEIGHT - 60 && y <= WINDOW_HEIGHT - 22) {
        g_money += 3000;
        g_feedLogs.insert(g_feedLogs.begin(), L"Выполнен быстрый фриланс: +$3,000 в кассу студии!");
        PlaySoundBeep(850, 40);
        InvalidateRect(hwnd, NULL, FALSE);
        return;
    }

    // Управление активной разработкой в офисе
    if (currentTab == TAB_OFFICE && g_isDevActive) {
        int devY = 480;
        // Охота на баги
        if (x >= 256 && x <= 426 && y >= devY + 62 && y <= devY + 90) {
            StartBugHunt();
            InvalidateRect(hwnd, NULL, FALSE);
            return;
        }
        // Кранч
        if (x >= 440 && x <= 600 && y >= devY + 62 && y <= devY + 90) {
            g_isCrunch = !g_isCrunch;
            PlaySoundBeep(g_isCrunch ? 1100 : 400, 50);
            InvalidateRect(hwnd, NULL, FALSE);
            return;
        }
        // Выпустить игру
        if (x >= 960 && x <= 1144 && y >= devY + 62 && y <= devY + 90) {
            FinishDevelopment();
            InvalidateRect(hwnd, NULL, FALSE);
            return;
        }
    }

    // Старт разработки в визарде
    if (currentTab == TAB_DEV_WIZARD) {
        if (x >= 270 && x <= 1010 && y >= 570 && y <= 620) {
            StartDevelopment();
            InvalidateRect(hwnd, NULL, FALSE);
            return;
        }
    }
}

// Обработка клавиатуры
void HandleKeyDown(WPARAM wParam, HWND hwnd) {
    if (g_showReviewDialog) {
        if (wParam == VK_RETURN || wParam == VK_SPACE) {
            g_showReviewDialog = false;
            currentTab = TAB_PORTFOLIO;
            InvalidateRect(hwnd, NULL, FALSE);
        }
        return;
    }

    if (g_showBugHuntDialog) {
        if (wParam == VK_ESCAPE) {
            g_showBugHuntDialog = false;
            InvalidateRect(hwnd, NULL, FALSE);
        }
        return;
    }

    switch (wParam) {
        case 'P':
            g_speed = (g_speed == 0 ? 1 : 0);
            break;
        case '1':
            if (currentTab == TAB_DEV_WIZARD) g_devGenreIdx = 0; else g_speed = 1;
            break;
        case '2':
            if (currentTab == TAB_DEV_WIZARD) g_devGenreIdx = 1; else g_speed = 2;
            break;
        case '3':
            if (currentTab == TAB_DEV_WIZARD) g_devGenreIdx = 2; else g_speed = 5;
            break;
        case '4':
            if (currentTab == TAB_DEV_WIZARD) g_devGenreIdx = 3;
            break;
        case '5':
            if (currentTab == TAB_DEV_WIZARD) g_devGenreIdx = 4;
            break;
        case '6':
            if (currentTab == TAB_DEV_WIZARD) g_devGenreIdx = 5;
            break;
        case 'Q': g_devThemeIdx = 0; break;
        case 'W': g_devThemeIdx = 1; break;
        case 'E':
            if (currentTab == TAB_ENGINES) {
                if (g_money >= 15000) {
                    g_money -= 15000;
                    CustomEngine eng;
                    eng.id = "titan_eng";
                    eng.name = L"Titan NextGen RayTracing";
                    eng.mult = 1.85;
                    eng.modules = {L"Рэйтрейсинг", L"Физика", L"Мультиплеер"};
                    eng.isProprietary = true;
                    g_engines.push_back(eng);
                    g_feedLogs.insert(g_feedLogs.begin(), L"Собран Titan NextGen Engine! Множитель x1.85!");
                    MessageBeep(MB_OK);
                }
            } else {
                g_devThemeIdx = 2;
            }
            break;
        case 'R':
            if (g_isDevActive) FinishDevelopment(); else g_devThemeIdx = 3;
            break;
        case 'T':
            if (currentTab == TAB_STAFF) {
                if (g_money >= 1500 && !g_staff.empty()) {
                    g_money -= 1500;
                    g_staff[0].code += 6;
                    g_staff[0].design += 5;
                    g_feedLogs.insert(g_feedLogs.begin(), L"Сотрудник прошел курс повышения квалификации (+6 Код, +5 Арт)!");
                    PlaySoundBeep(1000, 60);
                }
            } else {
                g_devThemeIdx = 4;
            }
            break;
        case 'Y': g_devThemeIdx = 5; break;
        case 'Z': g_devPlatformIdx = 0; break;
        case 'X': g_devPlatformIdx = 1; break;
        case 'C':
            if (g_isDevActive) g_isCrunch = !g_isCrunch; else g_devPlatformIdx = 2;
            break;
        case 'V': g_devPlatformIdx = 3; break;
        case 'N':
            currentTab = TAB_DEV_WIZARD;
            break;
        case 'F':
            g_money += 3000;
            g_feedLogs.insert(g_feedLogs.begin(), L"Выполнен фриланс заказ (+ $3,000)!");
            PlaySoundBeep(800, 40);
            break;
        case 'B':
            if (g_isDevActive) StartBugHunt();
            break;
        case VK_RETURN:
            if (currentTab == TAB_DEV_WIZARD) StartDevelopment();
            break;
    }

    InvalidateRect(hwnd, NULL, FALSE);
}

// Главная оконная процедура
LRESULT CALLBACK WndProc(HWND hwnd, UINT msg, WPARAM wParam, LPARAM lParam) {
    switch (msg) {
        case WM_CREATE:
            SetTimer(hwnd, 1, 1000, NULL);
            break;
        case WM_TIMER:
            if (g_showBugHuntDialog) {
                g_bugHuntTimer--;
                if (g_bugHuntTimer <= 0) {
                    g_showBugHuntDialog = false;
                }
                InvalidateRect(hwnd, NULL, FALSE);
                break;
            }
            if (g_speed > 0) {
                for (int i = 0; i < g_speed; i++) {
                    TickWeek();
                }
                InvalidateRect(hwnd, NULL, FALSE);
            }
            break;
        case WM_PAINT: {
            PAINTSTRUCT ps;
            HDC hdc = BeginPaint(hwnd, &ps);
            RECT rc;
            GetClientRect(hwnd, &rc);

            // Двойная буферизация для отсутствия мерцания
            HDC memDC = CreateCompatibleDC(hdc);
            HBITMAP memBitmap = CreateCompatibleBitmap(hdc, rc.right, rc.bottom);
            HBITMAP oldBitmap = (HBITMAP)SelectObject(memDC, memBitmap);

            DrawGame(memDC, rc);

            BitBlt(hdc, 0, 0, rc.right, rc.bottom, memDC, 0, 0, SRCCOPY);

            SelectObject(memDC, oldBitmap);
            DeleteObject(memBitmap);
            DeleteDC(memDC);

            EndPaint(hwnd, &ps);
            break;
        }
        case WM_LBUTTONDOWN: {
            int x = LOWORD(lParam);
            int y = HIWORD(lParam);
            HandleMouseClick(x, y, hwnd);
            break;
        }
        case WM_KEYDOWN:
            HandleKeyDown(wParam, hwnd);
            break;
        case WM_DESTROY:
            PostQuitMessage(0);
            break;
        default:
            return DefWindowProc(hwnd, msg, wParam, lParam);
    }
    return 0;
}

// Точка входа WinMain
int WINAPI WinMain(HINSTANCE hInstance, HINSTANCE hPrevInstance, LPSTR lpCmdLine, int nCmdShow) {
    GdiplusStartupInput gdiplusStartupInput;
    ULONG_PTR gdiplusToken;
    GdiplusStartup(&gdiplusToken, &gdiplusStartupInput, NULL);

    InitDatabase();

    WNDCLASSEXW wc = {0};
    wc.cbSize = sizeof(WNDCLASSEXW);
    wc.style = CS_HREDRAW | CS_VREDRAW;
    wc.lpfnWndProc = WndProc;
    wc.hInstance = hInstance;
    wc.hCursor = LoadCursor(NULL, IDC_ARROW);
    wc.hbrBackground = (HBRUSH)GetStockObject(BLACK_BRUSH);
    wc.lpszClassName = L"GameDevTycoonProNative";

    RegisterClassExW(&wc);

    HWND hwnd = CreateWindowExW(
        0,
        wc.lpszClassName,
        L"GameDev Tycoon: Studio Master Pro (Native C++ Edition)",
        WS_OVERLAPPED | WS_CAPTION | WS_SYSMENU | WS_MINIMIZEBOX,
        CW_USEDEFAULT, CW_USEDEFAULT,
        WINDOW_WIDTH, WINDOW_HEIGHT,
        NULL, NULL, hInstance, NULL
    );

    ShowWindow(hwnd, nCmdShow);
    UpdateWindow(hwnd);

    MSG msg;
    while (GetMessage(&msg, NULL, 0, 0)) {
        TranslateMessage(&msg);
        DispatchMessage(&msg);
    }

    GdiplusShutdown(gdiplusToken);
    return (int)msg.wParam;
}
