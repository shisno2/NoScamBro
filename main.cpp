#define NOMINMAX
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

#pragma comment(lib, "gdiplus.lib")
#pragma comment(lib, "gdi32.lib")
#pragma comment(lib, "winmm.lib")
#pragma comment(lib, "user32.lib")

using namespace Gdiplus;

// --- КОНСТАНТЫ ОКНА ---
const int WINDOW_WIDTH = 1320;
const int WINDOW_HEIGHT = 840;

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

enum IconType {
    ICON_OFFICE = 0,
    ICON_GAMEPAD,
    ICON_TROPHY,
    ICON_USERS,
    ICON_GEAR,
    ICON_RESEARCH,
    ICON_UPGRADE,
    ICON_ACHIEVEMENT,
    ICON_DOLLAR,
    ICON_HEART,
    ICON_RP,
    ICON_STOCK,
    ICON_CALENDAR,
    ICON_BUG,
    ICON_PLUS,
    ICON_BRIEFCASE,
    ICON_STAR,
    ICON_ROCKET,
    ICON_FIRE,
    ICON_CHECK,
    ICON_LOCK,
    ICON_PLAY,
    ICON_PAUSE,
    ICON_SPEED,
    ICON_CODE,
    ICON_ART,
    ICON_SOUND,
    ICON_DICE
};

TabIndex currentTab = TAB_OFFICE;

// Экономика и статистика
long long g_money = 35000;
long long g_fans = 50;
int g_rp = 30;
double g_stockPrice = 50.0;
double g_stockGrowth = 0.0;
int g_morale = 100;
int g_year = 1;
int g_month = 1;
int g_week = 1;
int g_speed = 1; // 0 = pause, 1 = 1x, 2 = 2x, 5 = 5x
int g_tickCounter = 0;

// Новые параметры студии
long long g_studioRating = 500; // Рейтинг студии
bool g_bonus10MAwarded = false; // Флаг мгновенного начисления $10,000,000,000
int g_hype = 25;               // Хайп студии (0-100%)
int g_brandTrust = 90;         // Репутация и доверие аудитории (0-100%)
int g_innovationIndex = 20;    // Индекс инноваций

int g_currentOfficeIdx = 0;

// Данные игры
std::vector<Genre> g_genres;
std::vector<Theme> g_themes;
std::vector<Platform> g_platforms;
std::vector<CustomEngine> g_engines;
std::vector<Office> g_offices;
std::vector<Employee> g_staff;
std::vector<Candidate> g_candidates;
std::vector<TechResearch> g_researches;
std::vector<ReleasedGame> g_games;
std::vector<Achievement> g_achievements;
std::vector<std::wstring> g_feedLogs;
std::vector<BugTarget> g_huntBugs;

// Текущая разработка
bool g_isDevActive = false;
std::wstring g_devTitle = L"Cyber Odyssey 2099";
int g_devGenreIdx = 0;
int g_devThemeIdx = 2; // Cyberpunk
int g_devPlatformIdx = 0;
int g_devEngineIdx = 0;
int g_devScale = 0; // 0: Indie, 1: AA, 2: AAA
int g_devMonetization = 0; // 0: Premium, 1: F2P, 2: MMO
int g_sliderGameplay = 50;
int g_sliderGraphics = 30;
int g_sliderSound = 20;
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

// Набор случайных названий игр
const std::vector<std::wstring> g_randomTitles = {
    L"Neon Horizon", L"Shadow Realm", L"Starlight Chronicles",
    L"Dragon's Legacy", L"Cyber Vanguard", L"Kingdom of Rust",
    L"Quantum Core", L"Solaris Odyssey", L"Apex Legends Tactics",
    L"Pixel Dungeon Crawler", L"Dusk of Eternity", L"Galactic Commander",
    L"Biohazard Outbreak", L"Medieval Dynasty Wars", L"Aetherial Echoes",
    L"Silicon Valley Mogul", L"Dark Space Rogue", L"Mythic Blade"
};

// Звуковые сигналы через Windows API
void PlaySoundBeep(int freq, int duration) {
    Beep(freq, duration);
}

// Форматирование больших чисел в компактный вид ($10.5B, 12.4M, 150k)
std::wstring FormatCompactMoney(long long val) {
    if (std::abs(val) >= 1000000000LL) {
        std::wstringstream ss;
        ss << (val < 0 ? L"-$" : L"$") << std::fixed << std::setprecision(2) << (std::abs(val) / 1000000000.0) << L"B";
        return ss.str();
    } else if (std::abs(val) >= 1000000LL) {
        std::wstringstream ss;
        ss << (val < 0 ? L"-$" : L"$") << std::fixed << std::setprecision(2) << (std::abs(val) / 1000000.0) << L"M";
        return ss.str();
    } else if (std::abs(val) >= 100000LL) {
        std::wstringstream ss;
        ss << (val < 0 ? L"-$" : L"$") << (std::abs(val) / 1000) << L"k";
        return ss.str();
    }
    std::wstringstream ss;
    ss << (val < 0 ? L"-$" : L"$") << std::abs(val);
    return ss.str();
}

std::wstring FormatCompactNumber(long long val) {
    if (val >= 1000000000LL) {
        std::wstringstream ss;
        ss << std::fixed << std::setprecision(2) << (val / 1000000000.0) << L"B";
        return ss.str();
    } else if (val >= 1000000LL) {
        std::wstringstream ss;
        ss << std::fixed << std::setprecision(2) << (val / 1000000.0) << L"M";
        return ss.str();
    } else if (val >= 10000LL) {
        std::wstringstream ss;
        ss << (val / 1000) << L"k";
        return ss.str();
    }
    return std::to_wstring(val);
}

// Проверка рейтинга студии и мгновенный супер-бонус
void CheckStudioRating() {
    if (!g_bonus10MAwarded && g_studioRating >= 10000000LL) {
        g_bonus10MAwarded = true;
        g_money += 10000000000LL; // Начисление 10 миллиардов $
        g_feedLogs.insert(g_feedLogs.begin(), L"💎 МЕГА-ДЖЕКПОТ! Рейтинг студии превысил 10,000,000! Начислено: +$10,000,000,000!");
        MessageBeep(MB_ICONASTERISK);
        PlaySoundBeep(1400, 100);
        PlaySoundBeep(1800, 150);
        PlaySoundBeep(2200, 250);
    }
}

// Инициализация базы данных
void InitDatabase() {
    g_genres = {
        {"rpg", L"RPG (Ролевая)", 2500, 0, {"fantasy", "scifi", "cyberpunk", "postapoc"}, 40, 35, 25, L"Глубокий сюжет, прокачка персонажей и открытый мир"},
        {"action", L"Экшен / Шутер", 3000, 0, {"scifi", "military", "cyberpunk", "zombie"}, 45, 35, 20, L"Динамичные перестрелки, адреналин и зрелищные спецэффекты"},
        {"strategy", L"RTS Стратегия", 3500, 20, {"history", "space", "medieval", "scifi"}, 50, 30, 20, L"Тактика, управление базами, ресурсами и армиями"},
        {"sim", L"Симулятор", 2000, 0, {"business", "city", "space"}, 45, 30, 25, L"Реалистичная физика, экономика и управление процессами"},
        {"horror", L"Survival Хоррор", 2800, 25, {"zombie", "mystery", "postapoc"}, 30, 35, 35, L"Мрачная атмосфера, ограниченные ресурсы и скримеры"},
        {"puzzle", L"Головоломка", 1200, 15, {"abstract", "fantasy", "space"}, 35, 45, 20, L"Увлекательные логические задачки и медитативный геймплей"}
    };

    g_themes = {
        {"fantasy", L"Фэнтези и Магия", 0},
        {"scifi", L"Научная фантастика", 0},
        {"cyberpunk", L"Киберпанк 2099", 20},
        {"postapoc", L"Постапокалипсис", 25},
        {"zombie", L"Зомби-эпидемия", 15},
        {"space", L"Космическая одиссея", 20},
        {"medieval", L"Средневековье", 0},
        {"business", L"Бизнес и Корпорации", 15}
    };

    g_platforms = {
        {"pc", L"ПК (Steam / EGS)", 1500, 1.0, 0},
        {"playbox", L"PlayBox 5 NextGen", 5000, 1.45, 30},
        {"switchy", L"Switchy Pro OLED", 3500, 1.25, 25},
        {"mobile", L"iOS & Android", 3000, 1.65, 20},
        {"vr", L"VR Matrix Headset", 8000, 0.95, 45}
    };

    g_engines = {
        {"basic", L"PixelCore 2D v1.0", 1.0, {L"2D Спрайты", L"Базовая физика"}, false},
        {"vortex", L"Vortex 3D Engine Pro", 1.45, {L"3D Освещение", L"ИИ врагов", L"Аудио-движок"}, true}
    };

    g_offices = {
        {"garage", L"Гараж родителей", 2, 0, 0, L"Уютный гараж. Хватит на двух энтузиастов и пару ПК."},
        {"coworking", L"Коворкинг в Центре", 4, 1500, 15000, L"Стильное рабочее пространство с быстрым оптоволокном и кофе."},
        {"studio", L"Собственная студия разработки", 6, 4500, 50000, L"Просторный лофт, переговорные и звукозаписывающая комната."},
        {"skyscraper", L"Небоскрёб GameDev Global", 8, 12000, 200000, L"Премиальная штаб-квартира мирового титана индустрии!"}
    };

    g_staff = {
        {1, L"Вы (Основатель)", L"Главный Геймдизайнер", 24, 22, 18, 0, 100, 0},
        {2, L"Максим Орлов", L"Senior Программист", 32, 12, 10, 1200, 100, 1}
    };

    g_candidates = {
        {101, L"Алиса Ветрова", L"Lead 3D Художник", 12, 34, 15, 1400, 3000, 2},
        {102, L"Дмитрий Смирнов", L"Саунд-дизайнер", 10, 14, 35, 1100, 2500, 3},
        {103, L"Егор Волков", L"AI & Physics Кодер", 36, 14, 12, 1600, 4000, 1},
        {104, L"Елена Соколова", L"Геймдизайнер уровней", 22, 28, 20, 1350, 3200, 0}
    };

    g_researches = {
        {"rtx", L"Трассировка лучей RayTracing 2.0", L"Увеличивает множитель очков графики на +25%", 35, false, L"Графика"},
        {"vr_kit", L"VR SDK & Neo Драйверы", L"Открывает платформу VR Matrix Headset", 45, false, L"Платформы"},
        {"synth", L"Оркестровый DSP Синтезатор", L"Увеличивает качество звука и музыкальных дорожек на +30%", 25, false, L"Звук"},
        {"neural_ai", L"Нейросетевой ИИ персонажей", L"Геймплей и механики получают +20% к рейтингу", 40, false, L"ИИ"},
        {"mmo_net", L"Сетевой стек MMO Server", L"Позволяет выпускать игры с MMO-монетизацией", 50, false, L"Онлайн"}
    };

    g_achievements = {
        {"first_game", L"Первый шаг в индустрии", L"Разработайте и выпустите свою первую коммерческую игру", 5000, 15, false},
        {"hit", L"Признание критиков (8.0+)", L"Получите средний балл рецензий 8.0 или выше", 12000, 25, false},
        {"masterpiece", L"Шедевр поколения (9.5+)", L"Создайте безупречную игру с оценкой от 9.5 баллов", 35000, 45, false},
        {"millionaire", L"Финансовый магнат", L"Заработайте свыше $1,000,000 совокупной выручки", 75000, 60, false},
        {"expansion", L"Расширение империи", L"Переедьте в Офис 2-го уровня или выше", 10000, 20, false},
        {"rating_10m", L"Легенда 10,000,000 Рейтинга", L"Наберите свыше 10,000,000 рейтинга студии", 100000000, 500, false}
    };

    g_feedLogs.push_back(L"🚀 Добро пожаловать в GameDev Studio Tycoon Pro (Native Edition)!");
    g_feedLogs.push_back(L"💡 Совет: Наберите 10,000,000 рейтинга студии, чтобы мгновенно получить $10,000,000,000!");
}

void CheckAchievements() {
    for (auto& a : g_achievements) {
        if (a.unlocked) continue;
        bool sat = false;
        if (a.id == "first_game" && g_games.size() >= 1) sat = true;
        if (a.id == "hit" && std::any_of(g_games.begin(), g_games.end(), [](const ReleasedGame& g){ return g.score >= 8.0; })) sat = true;
        if (a.id == "masterpiece" && std::any_of(g_games.begin(), g_games.end(), [](const ReleasedGame& g){ return g.score >= 9.5; })) sat = true;
        if (a.id == "expansion" && g_currentOfficeIdx >= 1) sat = true;
        if (a.id == "rating_10m" && g_studioRating >= 10000000LL) sat = true;
        if (a.id == "millionaire") {
            long long total = 0;
            for (auto& g : g_games) total += g.revenue;
            if (total >= 1000000) sat = true;
        }

        if (sat) {
            a.unlocked = true;
            g_money += a.rewardCash;
            g_rp += a.rewardRp;
            g_studioRating += 50000;
            g_feedLogs.insert(g_feedLogs.begin(), L"🏆 ДОСТИЖЕНИЕ: «" + a.title + L"» (+$" + std::to_wstring(a.rewardCash) + L", +" + std::to_wstring(a.rewardRp) + L" RP)!");
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
        MessageBoxW(NULL, L"Недостаточно средств для запуска разработки проекта!", L"Нехватка бюджета", MB_OK | MB_ICONWARNING);
        return;
    }

    g_money -= cost;
    g_devProgress = 0.0;
    g_devPtsCode = 0;
    g_devPtsDesign = 0;
    g_devPtsSound = 0;
    g_devPtsBugs = 0;
    g_isDevActive = true;

    g_hype = (std::min)(100, g_hype + 15);

    g_feedLogs.insert(g_feedLogs.begin(), L"🔥 Начата разработка игры: «" + g_devTitle + L"» (" + g_genres[g_devGenreIdx].name + L")");
    currentTab = TAB_OFFICE;
}

void FinishDevelopment() {
    if (!g_isDevActive) return;

    double scoreBase = 7.0;
    bool isSynergy = false;
    for (const auto& t : g_genres[g_devGenreIdx].bestThemes) {
        if (t == g_themes[g_devThemeIdx].id) { isSynergy = true; break; }
    }
    if (isSynergy) scoreBase = 8.8;

    double bugPenalty = g_devPtsBugs * 0.25;
    double bonusPts = (g_devPtsCode + g_devPtsDesign + g_devPtsSound) / 120.0;
    double rawScore = scoreBase + bonusPts - bugPenalty + ((rand() % 14 - 7) / 10.0);
    rawScore = (std::min)(10.0, (std::max)(2.0, rawScore));
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
    game.marketingMultiplier = 1.2 + (g_hype / 100.0);
    game.dlcCount = 0;
    game.audiencePool = (long long)(30000 * g_platforms[g_devPlatformIdx].audienceShare * std::pow(finalScore / 3.8, 3));

    g_games.insert(g_games.begin(), game);
    g_lastReviewedGame = game;

    g_lastReviewScores.clear();
    auto genReview = [finalScore](double offset) {
        double s = finalScore + offset + ((rand() % 8 - 4) / 10.0);
        return (std::min)(10.0, (std::max)(1.0, std::round(s * 10.0) / 10.0));
    };

    g_lastReviewScores.push_back({L"Игромания (RU)", genReview(0.0)});
    g_lastReviewScores.push_back({L"GameSpot (Global)", genReview(-0.1)});
    g_lastReviewScores.push_back({L"PC Gamer Pro", genReview(0.1)});
    g_lastReviewScores.push_back({L"IGN Worldwide", genReview(0.0)});

    int fansGain = (int)(std::pow(finalScore, 2.6) * 15 + g_fans * 0.12);
    g_fans += fansGain;
    g_rp += (int)(finalScore * 4.0);

    // Прирост рейтинга студии при релизе
    long long ratingBoost = (long long)(std::pow(finalScore, 3.2) * 150 + fansGain * 6 + g_hype * 250);
    g_studioRating += ratingBoost;

    if (finalScore >= 8.0) {
        g_brandTrust = (std::min)(100, g_brandTrust + 4);
    } else if (finalScore < 6.0) {
        g_brandTrust = (std::max)(20, g_brandTrust - 5);
    }

    g_isDevActive = false;
    g_showReviewDialog = true;
    MessageBeep(MB_OK);

    CheckStudioRating();
    CheckAchievements();
}

void StartBugHunt() {
    if (!g_isDevActive || g_devPtsBugs <= 0) return;
    g_showBugHuntDialog = true;
    g_bugHuntTimer = 10;
    g_bugsSquashed = 0;
    g_huntBugs.clear();

    int count = (std::min)(14, (std::max)(4, g_devPtsBugs));
    for (int i = 0; i < count; i++) {
        BugTarget b;
        b.x = (float)(40 + rand() % 540);
        b.y = (float)(40 + rand() % 320);
        b.size = 38.0f;
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
                g_money += (int)(eng.mult * 1100);
            }
        }
    }
    if (g_month > 12) {
        g_month = 1;
        g_year++;
        g_feedLogs.insert(g_feedLogs.begin(), L"🎉 Наступил " + std::to_wstring(g_year) + L"-й финансовый год студии!");
    }

    // Прогресс разработки
    if (g_isDevActive) {
        int tCode = 0, tDesign = 0, tSound = 0;
        for (const auto& s : g_staff) {
            tCode += s.code; tDesign += s.design; tSound += s.sound;
        }

        double mult = g_engines[g_devEngineIdx].mult;
        if (g_isCrunch) { mult *= 1.75; g_morale = (std::max)(10, g_morale - 1); }

        g_devPtsCode += (std::max)(1, (int)(tCode * (g_sliderGameplay / 40.0) * mult / 5.0));
        g_devPtsDesign += (std::max)(1, (int)(tDesign * (g_sliderGraphics / 30.0) * mult / 5.0));
        g_devPtsSound += (std::max)(1, (int)(tSound * (g_sliderSound / 30.0) * mult / 5.0));

        if (rand() % 100 < (g_isCrunch ? 50 : 25)) {
            g_devPtsBugs += (rand() % 2 + 1);
        }

        if (rand() % 100 < 30) g_rp++;

        double step = (tCode + tDesign + tSound) / (g_devScale == 2 ? 80.0 : (g_devScale == 1 ? 55.0 : 35.0));
        g_devProgress += step * (g_isCrunch ? 1.5 : 1.0);
        if (g_devProgress >= 100.0) {
            g_devProgress = 100.0;
        }
    }

    // Продажи игр
    for (auto& game : g_games) {
        if (game.weeksOnMarket > 32) continue;
        game.weeksOnMarket++;
        double decay = std::pow(0.89, game.weeksOnMarket);

        long long sold = 0;
        long long inc = 0;
        if (game.monetization == "f2p") {
            sold = (long long)(game.audiencePool * 0.35 * decay + g_fans * 0.2 * decay);
            inc = (long long)(sold * (2.8 + game.score * 0.6));
        } else {
            sold = (long long)(game.audiencePool * 0.16 * decay + g_fans * 0.06 * decay);
            inc = sold * game.price;
        }

        if (sold > 0) {
            game.copiesSold += sold;
            game.revenue += inc;
            g_money += inc;

            // Каждую неделю продажи дают дополнительный рейтинг студии!
            g_studioRating += (long long)(sold / 20 + 2);
        }
    }

    // Акции
    double delta = ((rand() % 24 - 11) / 10.0);
    if (g_money > 100000) delta += 0.8;
    if (g_money < 0) delta -= 1.5;
    g_stockPrice = (std::max)(5.0, g_stockPrice + delta);
    g_stockGrowth = delta;

    CheckStudioRating();
    CheckAchievements();
}

// --- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ОТРИСОВКИ GDI+ ---

GraphicsPath* CreateRoundedRectPath(float x, float y, float w, float h, float r) {
    GraphicsPath* path = new GraphicsPath();
    float d = r * 2.0f;
    if (d > w) d = w;
    if (d > h) d = h;

    path->AddArc(x, y, d, d, 180, 90);
    path->AddArc(x + w - d, y, d, d, 270, 90);
    path->AddArc(x + w - d, y + h - d, d, d, 0, 90);
    path->AddArc(x, y + h - d, d, d, 90, 90);
    path->CloseFigure();
    return path;
}

void FillRoundedRect(Graphics& g, Brush* brush, float x, float y, float w, float h, float r) {
    GraphicsPath* path = CreateRoundedRectPath(x, y, w, h, r);
    g.FillPath(brush, path);
    delete path;
}

void DrawRoundedRect(Graphics& g, Pen* pen, float x, float y, float w, float h, float r) {
    GraphicsPath* path = CreateRoundedRectPath(x, y, w, h, r);
    g.DrawPath(pen, path);
    delete path;
}

void FillGlassCard(Graphics& g, float x, float y, float w, float h, float r, Color bgTop, Color bgBottom, Color borderCol) {
    LinearGradientBrush grad(PointF(x, y), PointF(x, y + h), bgTop, bgBottom);
    FillRoundedRect(g, &grad, x, y, w, h, r);
    Pen pen(borderCol, 1.0f);
    DrawRoundedRect(g, &pen, x, y, w, h, r);
}

// Векторная отрисовка иконок (100% четкость без шрифтовых проблем)
void DrawVectorIcon(Graphics& g, IconType icon, float x, float y, float size, Color col) {
    SolidBrush brush(col);
    Pen pen(col, (std::max)(1.5f, size * 0.1f));
    pen.SetLineCap(LineCapRound, LineCapRound, DashCapRound);

    float cx = x + size / 2.0f;
    float cy = y + size / 2.0f;

    switch (icon) {
        case ICON_OFFICE: {
            g.FillRectangle(&brush, x + size * 0.15f, y + size * 0.15f, size * 0.7f, size * 0.75f);
            SolidBrush winBrush(Color(200, 10, 14, 23));
            for (int r = 0; r < 3; r++) {
                for (int c = 0; c < 3; c++) {
                    g.FillRectangle(&winBrush, x + size * (0.24f + c * 0.20f), y + size * (0.25f + r * 0.20f), size * 0.12f, size * 0.12f);
                }
            }
            break;
        }
        case ICON_GAMEPAD: {
            float r = size * 0.2f;
            FillRoundedRect(g, &brush, x + size * 0.05f, y + size * 0.25f, size * 0.9f, size * 0.5f, r);
            SolidBrush bDark(Color(255, 14, 18, 28));
            g.FillRectangle(&bDark, x + size * 0.2f, y + size * 0.42f, size * 0.18f, size * 0.16f);
            g.FillRectangle(&bDark, x + size * 0.25f, y + size * 0.35f, size * 0.08f, size * 0.30f);
            g.FillEllipse(&bDark, (REAL)(x + size * 0.65f), (REAL)(y + size * 0.36f), (REAL)(size * 0.12f), (REAL)(size * 0.12f));
            g.FillEllipse(&bDark, (REAL)(x + size * 0.75f), (REAL)(y + size * 0.48f), (REAL)(size * 0.12f), (REAL)(size * 0.12f));
            break;
        }
        case ICON_TROPHY: {
            PointF cupPts[4] = {
                PointF(x + size * 0.22f, y + size * 0.15f),
                PointF(x + size * 0.78f, y + size * 0.15f),
                PointF(x + size * 0.68f, y + size * 0.55f),
                PointF(x + size * 0.32f, y + size * 0.55f)
            };
            g.FillPolygon(&brush, cupPts, 4);
            g.FillRectangle(&brush, x + size * 0.44f, y + size * 0.55f, size * 0.12f, size * 0.22f);
            g.FillRectangle(&brush, x + size * 0.25f, y + size * 0.77f, size * 0.50f, size * 0.12f);
            g.DrawArc(&pen, x + size * 0.10f, y + size * 0.20f, size * 0.25f, size * 0.25f, 90, 180);
            g.DrawArc(&pen, x + size * 0.65f, y + size * 0.20f, size * 0.25f, size * 0.25f, 270, 180);
            break;
        }
        case ICON_USERS: {
            g.FillEllipse(&brush, (REAL)(cx - size * 0.15f), (REAL)(y + size * 0.12f), (REAL)(size * 0.30f), (REAL)(size * 0.30f));
            g.FillPie(&brush, (REAL)(cx - size * 0.35f), (REAL)(y + size * 0.45f), (REAL)(size * 0.70f), (REAL)(size * 0.50f), 180, 180);
            break;
        }
        case ICON_GEAR: {
            g.FillEllipse(&brush, (REAL)(cx - size * 0.32f), (REAL)(cy - size * 0.32f), (REAL)(size * 0.64f), (REAL)(size * 0.64f));
            for (int i = 0; i < 4; i++) {
                float angle = i * 45.0f * 3.14159f / 180.0f;
                float tx = cx + cos(angle) * size * 0.38f;
                float ty = cy + sin(angle) * size * 0.38f;
                g.FillRectangle(&brush, tx - size * 0.08f, ty - size * 0.08f, size * 0.16f, size * 0.16f);
            }
            SolidBrush bHole(Color(255, 18, 23, 35));
            g.FillEllipse(&bHole, (REAL)(cx - size * 0.14f), (REAL)(cy - size * 0.14f), (REAL)(size * 0.28f), (REAL)(size * 0.28f));
            break;
        }
        case ICON_RESEARCH: {
            PointF flaskPts[6] = {
                PointF(cx - size * 0.10f, y + size * 0.15f),
                PointF(cx + size * 0.10f, y + size * 0.15f),
                PointF(cx + size * 0.10f, y + size * 0.38f),
                PointF(cx + size * 0.40f, y + size * 0.85f),
                PointF(cx - size * 0.40f, y + size * 0.85f),
                PointF(cx - size * 0.10f, y + size * 0.38f)
            };
            g.FillPolygon(&brush, flaskPts, 6);
            break;
        }
        case ICON_UPGRADE: {
            PointF arrPts[7] = {
                PointF(cx, y + size * 0.12f),
                PointF(x + size * 0.80f, y + size * 0.48f),
                PointF(x + size * 0.60f, y + size * 0.48f),
                PointF(x + size * 0.60f, y + size * 0.85f),
                PointF(x + size * 0.40f, y + size * 0.85f),
                PointF(x + size * 0.40f, y + size * 0.48f),
                PointF(x + size * 0.20f, y + size * 0.48f)
            };
            g.FillPolygon(&brush, arrPts, 7);
            break;
        }
        case ICON_ACHIEVEMENT: {
            g.FillEllipse(&brush, (REAL)(cx - size * 0.42f), (REAL)(cy - size * 0.42f), (REAL)(size * 0.84f), (REAL)(size * 0.84f));
            SolidBrush bRing1(Color(255, 18, 23, 35));
            g.FillEllipse(&bRing1, (REAL)(cx - size * 0.28f), (REAL)(cy - size * 0.28f), (REAL)(size * 0.56f), (REAL)(size * 0.56f));
            g.FillEllipse(&brush, (REAL)(cx - size * 0.14f), (REAL)(cy - size * 0.14f), (REAL)(size * 0.28f), (REAL)(size * 0.28f));
            break;
        }
        case ICON_DOLLAR: {
            g.FillEllipse(&brush, (REAL)(cx - size * 0.42f), (REAL)(cy - size * 0.42f), (REAL)(size * 0.84f), (REAL)(size * 0.84f));
            SolidBrush bText(Color(255, 12, 16, 26));
            Font font(&FontFamily(L"Segoe UI"), size * 0.52f, FontStyleBold, UnitPixel);
            StringFormat sf;
            sf.SetAlignment(StringAlignmentCenter);
            sf.SetLineAlignment(StringAlignmentCenter);
            RectF rf(x, y - size * 0.03f, size, size);
            g.DrawString(L"$", -1, &font, rf, &sf, &bText);
            break;
        }
        case ICON_HEART: {
            g.FillEllipse(&brush, (REAL)(cx - size * 0.38f), (REAL)(cy - size * 0.32f), (REAL)(size * 0.40f), (REAL)(size * 0.40f));
            g.FillEllipse(&brush, (REAL)(cx - size * 0.02f), (REAL)(cy - size * 0.32f), (REAL)(size * 0.40f), (REAL)(size * 0.40f));
            PointF tri[3] = {
                PointF(cx - size * 0.38f, cy - size * 0.08f),
                PointF(cx + size * 0.38f, cy - size * 0.08f),
                PointF(cx, cy + size * 0.40f)
            };
            g.FillPolygon(&brush, tri, 3);
            break;
        }
        case ICON_RP: {
            PointF gem[4] = {
                PointF(cx, y + size * 0.10f),
                PointF(x + size * 0.82f, cy),
                PointF(cx, y + size * 0.90f),
                PointF(x + size * 0.18f, cy)
            };
            g.FillPolygon(&brush, gem, 4);
            break;
        }
        case ICON_STOCK: {
            PointF chart[4] = {
                PointF(x + size * 0.15f, y + size * 0.75f),
                PointF(x + size * 0.40f, y + size * 0.50f),
                PointF(x + size * 0.65f, y + size * 0.60f),
                PointF(x + size * 0.85f, y + size * 0.20f)
            };
            g.DrawLines(&pen, chart, 4);
            g.FillEllipse(&brush, (REAL)(x + size * 0.80f), (REAL)(y + size * 0.15f), (REAL)(size * 0.18f), (REAL)(size * 0.18f));
            break;
        }
        case ICON_CALENDAR: {
            FillRoundedRect(g, &brush, x + size * 0.15f, y + size * 0.20f, size * 0.70f, size * 0.65f, size * 0.10f);
            SolidBrush bHole(Color(255, 18, 23, 35));
            g.FillRectangle(&bHole, x + size * 0.22f, y + size * 0.42f, size * 0.56f, size * 0.36f);
            g.FillRectangle(&brush, x + size * 0.28f, y + size * 0.10f, size * 0.10f, size * 0.18f);
            g.FillRectangle(&brush, x + size * 0.62f, y + size * 0.10f, size * 0.10f, size * 0.18f);
            break;
        }
        case ICON_BUG: {
            g.FillEllipse(&brush, (REAL)(cx - size * 0.25f), (REAL)(cy - size * 0.30f), (REAL)(size * 0.50f), (REAL)(size * 0.60f));
            g.DrawLine(&pen, cx - size * 0.35f, cy - size * 0.15f, cx + size * 0.35f, cy - size * 0.15f);
            g.DrawLine(&pen, cx - size * 0.38f, cy + size * 0.05f, cx + size * 0.38f, cy + size * 0.05f);
            g.DrawLine(&pen, cx - size * 0.35f, cy + size * 0.25f, cx + size * 0.35f, cy + size * 0.25f);
            break;
        }
        case ICON_PLUS: {
            float th = size * 0.22f;
            g.FillRectangle(&brush, cx - th * 0.5f, y + size * 0.15f, th, size * 0.70f);
            g.FillRectangle(&brush, x + size * 0.15f, cy - th * 0.5f, size * 0.70f, th);
            break;
        }
        case ICON_BRIEFCASE: {
            FillRoundedRect(g, &brush, x + size * 0.15f, y + size * 0.32f, size * 0.70f, size * 0.55f, size * 0.10f);
            g.DrawArc(&pen, cx - size * 0.20f, y + size * 0.18f, size * 0.40f, size * 0.30f, 180, 180);
            break;
        }
        case ICON_STAR: {
            PointF star[10];
            for (int i = 0; i < 10; i++) {
                float r = (i % 2 == 0) ? size * 0.42f : size * 0.18f;
                float a = (i * 36.0f - 90.0f) * 3.14159f / 180.0f;
                star[i] = PointF(cx + cos(a) * r, cy + sin(a) * r);
            }
            g.FillPolygon(&brush, star, 10);
            break;
        }
        case ICON_ROCKET: {
            PointF rock[5] = {
                PointF(cx, y + size * 0.10f),
                PointF(cx + size * 0.28f, y + size * 0.60f),
                PointF(cx + size * 0.18f, y + size * 0.85f),
                PointF(cx - size * 0.18f, y + size * 0.85f),
                PointF(cx - size * 0.28f, y + size * 0.60f)
            };
            g.FillPolygon(&brush, rock, 5);
            break;
        }
        case ICON_FIRE: {
            PointF flame[5] = {
                PointF(cx, y + size * 0.10f),
                PointF(cx + size * 0.35f, y + size * 0.55f),
                PointF(cx + size * 0.20f, y + size * 0.88f),
                PointF(cx - size * 0.20f, y + size * 0.88f),
                PointF(cx - size * 0.35f, y + size * 0.55f)
            };
            g.FillPolygon(&brush, flame, 5);
            break;
        }
        case ICON_CHECK: {
            PointF chk[3] = {
                PointF(x + size * 0.18f, cy),
                PointF(x + size * 0.42f, y + size * 0.75f),
                PointF(x + size * 0.85f, y + size * 0.25f)
            };
            g.DrawLines(&pen, chk, 3);
            break;
        }
        case ICON_LOCK: {
            FillRoundedRect(g, &brush, x + size * 0.20f, y + size * 0.42f, size * 0.60f, size * 0.48f, size * 0.08f);
            g.DrawArc(&pen, cx - size * 0.20f, y + size * 0.18f, size * 0.40f, size * 0.40f, 180, 180);
            break;
        }
        case ICON_PLAY: {
            PointF ply[3] = {
                PointF(x + size * 0.25f, y + size * 0.18f),
                PointF(x + size * 0.80f, cy),
                PointF(x + size * 0.25f, y + size * 0.82f)
            };
            g.FillPolygon(&brush, ply, 3);
            break;
        }
        case ICON_PAUSE: {
            g.FillRectangle(&brush, x + size * 0.22f, y + size * 0.20f, size * 0.20f, size * 0.60f);
            g.FillRectangle(&brush, x + size * 0.58f, y + size * 0.20f, size * 0.20f, size * 0.60f);
            break;
        }
        case ICON_SPEED: {
            PointF spd1[3] = { PointF(x + size * 0.15f, y + size * 0.20f), PointF(x + size * 0.52f, cy), PointF(x + size * 0.15f, y + size * 0.80f) };
            PointF spd2[3] = { PointF(x + size * 0.48f, y + size * 0.20f), PointF(x + size * 0.85f, cy), PointF(x + size * 0.48f, y + size * 0.80f) };
            g.FillPolygon(&brush, spd1, 3);
            g.FillPolygon(&brush, spd2, 3);
            break;
        }
        case ICON_CODE: {
            PointF lft[3] = { PointF(cx - size * 0.12f, y + size * 0.25f), PointF(cx - size * 0.38f, cy), PointF(cx - size * 0.12f, y + size * 0.75f) };
            PointF rgt[3] = { PointF(cx + size * 0.12f, y + size * 0.25f), PointF(cx + size * 0.38f, cy), PointF(cx + size * 0.12f, y + size * 0.75f) };
            g.DrawLines(&pen, lft, 3);
            g.DrawLines(&pen, rgt, 3);
            break;
        }
        case ICON_ART: {
            g.FillEllipse(&brush, (REAL)(cx - size * 0.38f), (REAL)(cy - size * 0.38f), (REAL)(size * 0.76f), (REAL)(size * 0.76f));
            SolidBrush bHole(Color(255, 18, 23, 35));
            g.FillEllipse(&bHole, (REAL)(cx + size * 0.10f), (REAL)(cy + size * 0.10f), (REAL)(size * 0.18f), (REAL)(size * 0.18f));
            break;
        }
        case ICON_SOUND: {
            PointF snd[4] = { PointF(x + size * 0.20f, y + size * 0.35f), PointF(x + size * 0.42f, y + size * 0.35f), PointF(x + size * 0.65f, y + size * 0.15f), PointF(x + size * 0.65f, y + size * 0.85f) };
            g.FillPolygon(&brush, snd, 4);
            g.DrawArc(&pen, x + size * 0.50f, y + size * 0.25f, size * 0.40f, size * 0.50f, 300, 120);
            break;
        }
        case ICON_DICE: {
            FillRoundedRect(g, &brush, x + size * 0.15f, y + size * 0.15f, size * 0.70f, size * 0.70f, size * 0.15f);
            SolidBrush bDot(Color(255, 18, 23, 35));
            g.FillEllipse(&bDot, (REAL)(cx - size * 0.08f), (REAL)(cy - size * 0.08f), (REAL)(size * 0.16f), (REAL)(size * 0.16f));
            g.FillEllipse(&bDot, (REAL)(x + size * 0.28f), (REAL)(y + size * 0.28f), (REAL)(size * 0.14f), (REAL)(size * 0.14f));
            g.FillEllipse(&bDot, (REAL)(x + size * 0.58f), (REAL)(y + size * 0.58f), (REAL)(size * 0.14f), (REAL)(size * 0.14f));
            break;
        }
    }
}

// Полоса навыка сотрудника
void DrawSkillBar(Graphics& g, const wchar_t* label, int val, int maxVal, float x, float y, float w, Color barCol, Font* font) {
    SolidBrush textBrush(Color(255, 160, 170, 190));
    g.DrawString(label, -1, font, PointF(x, y - 1), &textBrush);

    float barX = x + 46;
    float barW = w - 85;
    float barH = 7.0f;

    SolidBrush bgTrack(Color(255, 20, 26, 38));
    FillRoundedRect(g, &bgTrack, barX, y + 4, barW, barH, 3.0f);

    float fillW = barW * ((std::min)(1.0f, (float)val / (float)maxVal));
    if (fillW > 2) {
        SolidBrush barBrush(barCol);
        FillRoundedRect(g, &barBrush, barX, y + 4, fillW, barH, 3.0f);
    }

    std::wstring valStr = std::to_wstring(val);
    SolidBrush numBrush(Color(255, 225, 230, 245));
    g.DrawString(valStr.c_str(), -1, font, PointF(barX + barW + 8, y - 1), &numBrush);
}

// --- ГЛАВНАЯ ФУНКЦИЯ ОТРИСОВКИ ---
void DrawGame(HDC hdc, RECT rc) {
    Graphics g(hdc);
    g.SetSmoothingMode(SmoothingModeAntiAlias);
    g.SetTextRenderingHint(TextRenderingHintClearTypeGridFit);

    // Задний фон окна
    LinearGradientBrush bgWindow(PointF(0, 0), PointF(0, (float)rc.bottom), Color(255, 11, 14, 22), Color(255, 15, 20, 31));
    g.FillRectangle(&bgWindow, 0, 0, rc.right, rc.bottom);

    // Шрифты
    FontFamily ff(L"Segoe UI");
    Font fontHuge(&ff, 28, FontStyleBold, UnitPixel);
    Font fontBig(&ff, 18, FontStyleBold, UnitPixel);
    Font fontTitle(&ff, 14, FontStyleBold, UnitPixel);
    Font fontBody(&ff, 12, FontStyleRegular, UnitPixel);
    Font fontBold(&ff, 12, FontStyleBold, UnitPixel);
    Font fontSmall(&ff, 11, FontStyleRegular, UnitPixel);
    Font fontMicro(&ff, 10, FontStyleRegular, UnitPixel);

    // Палитра
    Color colWhite(255, 248, 250, 252);
    Color colMuted(255, 148, 163, 184);
    Color colCardBorder(255, 38, 48, 70);
    Color colCardTop(255, 22, 28, 43);
    Color colCardBot(255, 17, 22, 34);

    Color colIndigo(255, 99, 102, 241);
    Color colEmerald(255, 16, 185, 129);
    Color colCyan(255, 6, 182, 212);
    Color colAmber(255, 245, 158, 11);
    Color colRose(255, 244, 63, 94);
    Color colPurple(255, 168, 85, 247);

    SolidBrush textWhite(colWhite);
    SolidBrush textMuted(colMuted);

    // ==========================================
    // 1. ВЕРХНЯЯ ПАНЕЛЬ СТАТИСТИКИ (HEADER)
    // ==========================================
    float topH = 74.0f;
    LinearGradientBrush topBg(PointF(0, 0), PointF(0, topH), Color(255, 18, 24, 38), Color(255, 13, 17, 27));
    g.FillRectangle(&topBg, 0, 0, rc.right, (INT)topH);

    Pen topBorder(Color(255, 42, 54, 78), 1.0f);
    g.DrawLine(&topBorder, 0, (INT)topH, rc.right, (INT)topH);

    // Логотип и Название студии
    FillGlassCard(g, 16, 14, 46, 46, 10, colIndigo, Color(255, 79, 70, 229), Color(255, 129, 140, 248));
    DrawVectorIcon(g, ICON_GAMEPAD, 24, 22, 30, colWhite);

    g.DrawString(L"PIXEL FORGE STUDIOS", -1, &fontTitle, PointF(72, 16), &textWhite);
    std::wstring tierStr = g_offices[g_currentOfficeIdx].name + L" • Ур." + std::to_wstring(g_currentOfficeIdx + 1);
    SolidBrush accentBrand(Color(255, 165, 180, 252));
    g.DrawString(tierStr.c_str(), -1, &fontSmall, PointF(72, 38), &accentBrand);

    // ЧИПЫ СТАТИСТИКИ (СПРАВА)
    auto drawStatChip = [&](float x, float w, IconType icon, Color iconCol, const std::wstring& val, const std::wstring& label, Color valCol, bool isSpecial = false) {
        if (isSpecial) {
            FillGlassCard(g, x, 14, w, 46, 8, Color(255, 45, 36, 16), Color(255, 28, 22, 10), colAmber);
        } else {
            FillGlassCard(g, x, 14, w, 46, 8, colCardTop, colCardBot, colCardBorder);
        }
        DrawVectorIcon(g, icon, x + 8, 24, 24, iconCol);
        SolidBrush bVal(valCol);
        g.DrawString(val.c_str(), -1, &fontBold, PointF(x + 36, 17), &bVal);
        g.DrawString(label.c_str(), -1, &fontMicro, PointF(x + 36, 38), &textMuted);
    };

    // 1. Баланс студии
    drawStatChip(280, 130, ICON_DOLLAR, colEmerald, FormatCompactMoney(g_money), L"Баланс студии", g_money < 0 ? colRose : colEmerald);

    // 2. РЕЙТИНГ СТУДИИ (Новый ключевой параметр с джекпотом на 10M)
    bool isRatingHigh = (g_studioRating >= 10000000LL);
    std::wstring ratingStr = FormatCompactNumber(g_studioRating);
    drawStatChip(418, 135, ICON_STAR, isRatingHigh ? colAmber : colAmber, ratingStr, isRatingHigh ? L"★ ТОП-1 МИРА" : L"Рейтинг студии", isRatingHigh ? colEmerald : colAmber, isRatingHigh);

    // 3. Поклонники (Фанаты)
    drawStatChip(561, 115, ICON_HEART, colRose, FormatCompactNumber(g_fans), L"Поклонники", colRose);

    // 4. Очки исследований (RP)
    std::wstringstream ssRp;
    ssRp << g_rp << L" RP";
    drawStatChip(684, 110, ICON_RP, colCyan, ssRp.str(), L"Наука (RP)", colCyan);

    // 5. Акции студии
    drawStatChip(802, 125, ICON_STOCK, colPurple, FormatCompactMoney((long long)g_stockPrice), L"Акции студии", colPurple);

    // 6. Календарь
    std::wstringstream ssDate;
    ssDate << L"Г." << g_year << L" М." << g_month << L" Н." << g_week;
    drawStatChip(935, 125, ICON_CALENDAR, colAmber, ssDate.str(), L"Календарь", colWhite);

    // 7. Кнопки управления скоростью (⏸, 1x, 2x, 5x)
    float spX = 1070.0f;
    FillGlassCard(g, spX, 14, 230, 46, 8, colCardTop, colCardBot, colCardBorder);

    struct SpeedBtn { int spd; const wchar_t* txt; IconType ic; };
    SpeedBtn sbtns[4] = {
        {0, L"||", ICON_PAUSE},
        {1, L"1x", ICON_PLAY},
        {2, L"2x", ICON_SPEED},
        {5, L"5x", ICON_SPEED}
    };

    for (int i = 0; i < 4; i++) {
        float bx = spX + 8 + i * 53;
        bool isActive = (g_speed == sbtns[i].spd);
        if (isActive) {
            FillGlassCard(g, bx, 20, 48, 34, 6, colIndigo, Color(255, 79, 70, 229), Color(255, 165, 180, 252));
        } else {
            FillGlassCard(g, bx, 20, 48, 34, 6, Color(255, 25, 32, 48), Color(255, 20, 26, 38), colCardBorder);
        }
        SolidBrush bTxt(isActive ? colWhite : colMuted);
        StringFormat sf;
        sf.SetAlignment(StringAlignmentCenter);
        sf.SetLineAlignment(StringAlignmentCenter);
        g.DrawString(sbtns[i].txt, -1, &fontBold, RectF(bx, 20, 48, 34), &sf, &bTxt);
    }

    // ==========================================
    // 2. БОКОВОЕ МЕНЮ (САЙДБАР)
    // ==========================================
    float sideW = 215.0f;
    LinearGradientBrush sideBg(PointF(0, topH), PointF(sideW, topH), Color(255, 16, 21, 33), Color(255, 14, 18, 28));
    g.FillRectangle(&sideBg, 0, (INT)topH, (INT)sideW, rc.bottom - (INT)topH);
    g.DrawLine(&topBorder, (INT)sideW, (INT)topH, (INT)sideW, rc.bottom);

    struct TabItem { TabIndex tab; const wchar_t* title; IconType icon; };
    TabItem navItems[8] = {
        {TAB_OFFICE, L"Офис студии", ICON_OFFICE},
        {TAB_DEV_WIZARD, L"Новая игра", ICON_GAMEPAD},
        {TAB_PORTFOLIO, L"Портфолио игр", ICON_TROPHY},
        {TAB_STAFF, L"Персонал & Найм", ICON_USERS},
        {TAB_ENGINES, L"Движки игр", ICON_GEAR},
        {TAB_RESEARCH, L"Исследования", ICON_RESEARCH},
        {TAB_UPGRADES, L"Улучшения офиса", ICON_UPGRADE},
        {TAB_ACHIEVEMENTS, L"Достижения", ICON_ACHIEVEMENT}
    };

    for (int i = 0; i < 8; i++) {
        float ny = topH + 16 + i * 46;
        bool isActive = (currentTab == navItems[i].tab);

        if (isActive) {
            FillGlassCard(g, 12, ny, sideW - 24, 38, 8, Color(255, 99, 102, 241), Color(255, 79, 70, 229), Color(255, 165, 180, 252));
            DrawVectorIcon(g, navItems[i].icon, 24, ny + 9, 20, colWhite);
            g.DrawString(navItems[i].title, -1, &fontBold, PointF(52, ny + 9), &textWhite);
            SolidBrush dotBrush(Color(255, 255, 255, 255));
            g.FillEllipse(&dotBrush, (REAL)(sideW - 28), (REAL)(ny + 15), 6.0f, 6.0f);
        } else {
            DrawVectorIcon(g, navItems[i].icon, 24, ny + 9, 20, colMuted);
            g.DrawString(navItems[i].title, -1, &fontBody, PointF(52, ny + 9), &textMuted);
        }
    }

    // Быстрые кнопки внизу сайдбара
    float qy1 = (float)rc.bottom - 105.0f;
    FillGlassCard(g, 12, qy1, sideW - 24, 42, 8, Color(255, 99, 102, 241), Color(255, 67, 56, 202), Color(255, 165, 180, 252));
    DrawVectorIcon(g, ICON_PLUS, 22, qy1 + 11, 20, colWhite);
    g.DrawString(L"Создать игру [N]", -1, &fontBold, PointF(48, qy1 + 11), &textWhite);

    float qy2 = (float)rc.bottom - 55.0f;
    FillGlassCard(g, 12, qy2, sideW - 24, 40, 8, Color(255, 16, 36, 48), Color(255, 12, 26, 36), Color(255, 6, 182, 212));
    DrawVectorIcon(g, ICON_BRIEFCASE, 22, qy2 + 10, 18, colCyan);
    SolidBrush bCyan(colCyan);
    g.DrawString(L"Фриланс +$3k [F]", -1, &fontBold, PointF(48, qy2 + 10), &bCyan);

    // ==========================================
    // 3. ОСНОВНОЙ КОНТЕНТНЫЙ БЛОК
    // ==========================================
    float cx = sideW + 20.0f;
    float cy = topH + 16.0f;
    float cw = (float)rc.right - cx - 20.0f;

    // --- ВКЛАДКА 0: ОФИС СТУДИИ ---
    if (currentTab == TAB_OFFICE) {
        g.DrawString(L"Главный офис разработки", -1, &fontBig, PointF(cx, cy), &textWhite);
        
        std::wstringstream ssSubInfo;
        ssSubInfo << L"Сотрудников: " << g_staff.size() << L" / " << g_offices[g_currentOfficeIdx].capacity 
                  << L"   |   Рейтинг студии: " << g_studioRating << L" / 10,000,000"
                  << L"   |   Хайп: " << g_hype << L"%   |   Доверие: " << g_brandTrust << L"%";
        g.DrawString(ssSubInfo.str().c_str(), -1, &fontSmall, PointF(cx, cy + 26), &textMuted);

        // Интерактивная зона столов сотрудников
        float roomY = cy + 52.0f;
        float roomH = 300.0f;
        FillGlassCard(g, cx, roomY, cw, roomH, 12, colCardTop, colCardBot, colCardBorder);

        int capacity = g_offices[g_currentOfficeIdx].capacity;
        float deskW = (cw - 50.0f) / 4.0f;
        float deskH = 126.0f;

        for (size_t i = 0; i < (size_t)capacity; i++) {
            float dx = cx + 16.0f + (i % 4) * (deskW + 10.0f);
            float dy = roomY + 16.0f + (i / 4) * (deskH + 14.0f);

            if (i < g_staff.size()) {
                FillGlassCard(g, dx, dy, deskW, deskH, 10, Color(255, 26, 34, 52), Color(255, 19, 25, 39), Color(255, 50, 64, 95));

                Color avatarCols[4] = {colAmber, colCyan, colPurple, colEmerald};
                Color avCol = avatarCols[g_staff[i].avatarColorIdx % 4];
                FillRoundedRect(g, &SolidBrush(avCol), dx + 10, dy + 10, 32, 32, 6);
                DrawVectorIcon(g, ICON_USERS, dx + 15, dy + 15, 22, Color(255, 15, 20, 30));

                g.DrawString(g_staff[i].name.c_str(), -1, &fontBold, PointF(dx + 48, dy + 9), &textWhite);
                SolidBrush bRole(avCol);
                g.DrawString(g_staff[i].role.c_str(), -1, &fontMicro, PointF(dx + 48, dy + 27), &bRole);

                DrawSkillBar(g, L"Код", g_staff[i].code, 50, dx + 10, dy + 48, deskW - 20, colCyan, &fontSmall);
                DrawSkillBar(g, L"Арт", g_staff[i].design, 50, dx + 10, dy + 66, deskW - 20, colPurple, &fontSmall);
                DrawSkillBar(g, L"Звук", g_staff[i].sound, 50, dx + 10, dy + 84, deskW - 20, colAmber, &fontSmall);

                std::wstring salStr = L"$" + std::to_wstring(g_staff[i].salary) + L"/мес";
                SolidBrush bSal(colEmerald);
                g.DrawString(salStr.c_str(), -1, &fontMicro, PointF(dx + 10, dy + 104), &bSal);

                SolidBrush bDot(colEmerald);
                g.FillEllipse(&bDot, (REAL)(dx + deskW - 22), (REAL)(dy + 107), 6.0f, 6.0f);
            } else {
                Pen dashed(Color(255, 45, 58, 85), 1.5f);
                dashed.SetDashStyle(DashStyleDash);
                DrawRoundedRect(g, &dashed, dx, dy, deskW, deskH, 10);

                DrawVectorIcon(g, ICON_PLUS, dx + deskW / 2 - 14, dy + 28, 28, colMuted);
                StringFormat sf;
                sf.SetAlignment(StringAlignmentCenter);
                g.DrawString(L"Свободное место", -1, &fontSmall, RectF(dx, dy + 62, deskW, 20), &sf, &textMuted);
                SolidBrush bHire(colIndigo);
                g.DrawString(L"[Клик: Нанять]", -1, &fontBold, RectF(dx, dy + 82, deskW, 20), &sf, &bHire);
            }
        }

        // ПАНЕЛЬ ТЕКУЩЕЙ РАЗРАБОТКИ
        float devY = roomY + roomH + 14.0f;
        if (g_isDevActive) {
            float devH = 120.0f;
            FillGlassCard(g, cx, devY, cw, devH, 12, Color(255, 28, 32, 54), Color(255, 18, 22, 38), Color(255, 99, 102, 241));

            std::wstring dTitle = L"РАЗРАБОТКА: «" + g_devTitle + L"» • " + g_genres[g_devGenreIdx].name;
            g.DrawString(dTitle.c_str(), -1, &fontBold, PointF(cx + 18, devY + 12), &textWhite);

            auto drawPtBadge = [&](float bx, const wchar_t* lbl, int pts, Color col, IconType ic) {
                FillGlassCard(g, bx, devY + 10, 110, 26, 6, Color(255, 20, 25, 40), Color(255, 15, 20, 32), col);
                DrawVectorIcon(g, ic, bx + 6, devY + 15, 16, col);
                std::wstring s = std::wstring(lbl) + L": " + std::to_wstring(pts);
                SolidBrush b(col);
                g.DrawString(s.c_str(), -1, &fontSmall, PointF(bx + 26, devY + 14), &b);
            };

            drawPtBadge(cx + 460, L"Код", g_devPtsCode, colCyan, ICON_CODE);
            drawPtBadge(cx + 580, L"Арт", g_devPtsDesign, colPurple, ICON_ART);
            drawPtBadge(cx + 700, L"Звук", g_devPtsSound, colAmber, ICON_SOUND);
            drawPtBadge(cx + 820, L"Баги", g_devPtsBugs, g_devPtsBugs > 5 ? colRose : colEmerald, ICON_BUG);

            float progW = cw - 36.0f;
            FillRoundedRect(g, &SolidBrush(Color(255, 12, 16, 26)), cx + 18, devY + 44, progW, 16, 8);

            float fillProg = progW * ((float)g_devProgress / 100.0f);
            if (fillProg > 4) {
                LinearGradientBrush progGrad(PointF(cx + 18, 0), PointF(cx + 18 + progW, 0), colIndigo, colEmerald);
                FillRoundedRect(g, &progGrad, cx + 18, devY + 44, fillProg, 16, 8);
            }

            std::wstring prgStr = std::to_wstring((int)g_devProgress) + L"% Завершено";
            SolidBrush bProg(colWhite);
            g.DrawString(prgStr.c_str(), -1, &fontMicro, PointF(cx + 24, devY + 45), &bProg);

            // Кнопки
            FillGlassCard(g, cx + 18, devY + 70, 180, 36, 8, Color(255, 220, 38, 38), Color(255, 185, 28, 28), Color(255, 248, 113, 113));
            DrawVectorIcon(g, ICON_BUG, cx + 28, devY + 78, 20, colWhite);
            g.DrawString(L"Охота на баги [B]", -1, &fontBold, PointF(cx + 54, devY + 78), &textWhite);

            if (g_isCrunch) {
                FillGlassCard(g, cx + 210, devY + 70, 170, 36, 8, Color(255, 234, 88, 12), Color(255, 194, 65, 12), Color(255, 251, 146, 60));
            } else {
                FillGlassCard(g, cx + 210, devY + 70, 170, 36, 8, Color(255, 30, 38, 58), Color(255, 22, 28, 44), colCardBorder);
            }
            DrawVectorIcon(g, ICON_FIRE, cx + 220, devY + 78, 20, colWhite);
            g.DrawString(L"Кранч x2 [C]", -1, &fontBold, PointF(cx + 248, devY + 78), &textWhite);

            bool canRelease = (g_devProgress >= 100.0);
            if (canRelease) {
                FillGlassCard(g, cx + cw - 240, devY + 70, 222, 36, 8, colEmerald, Color(255, 5, 150, 105), Color(255, 110, 231, 183));
            } else {
                FillGlassCard(g, cx + cw - 240, devY + 70, 222, 36, 8, Color(255, 30, 38, 58), Color(255, 22, 28, 44), colCardBorder);
            }
            DrawVectorIcon(g, ICON_ROCKET, cx + cw - 230, devY + 78, 20, colWhite);
            g.DrawString(L"Выпустить игру! [R]", -1, &fontBold, PointF(cx + cw - 202, devY + 78), &textWhite);
        }

        // ЛЕНТА СОБЫТИЙ
        float logY = devY + (g_isDevActive ? 134.0f : 0.0f);
        float logH = (float)rc.bottom - logY - 16.0f;
        FillGlassCard(g, cx, logY, cw, logH, 12, colCardTop, colCardBot, colCardBorder);

        g.DrawString(L"Информационная лента студии:", -1, &fontBold, PointF(cx + 18, logY + 12), &textWhite);

        size_t maxLogs = (size_t)(std::max)(2, (int)(logH - 45) / 22);
        for (size_t i = 0; i < (std::min)(maxLogs, g_feedLogs.size()); i++) {
            float ly = logY + 36.0f + i * 22.0f;
            SolidBrush bulletBrush(colAmber);
            g.FillEllipse(&bulletBrush, (REAL)(cx + 20), (REAL)(ly + 5), 6.0f, 6.0f);
            SolidBrush bLog(i == 0 ? colWhite : colMuted);
            g.DrawString(g_feedLogs[i].c_str(), -1, &fontSmall, PointF(cx + 34, ly), &bLog);
        }
    }

    // --- ВКЛАДКА 1: КОНСТРУКТОР НОВОЙ ИГРЫ ---
    else if (currentTab == TAB_DEV_WIZARD) {
        g.DrawString(L"Конструктор новой игры", -1, &fontBig, PointF(cx, cy), &textWhite);
        g.DrawString(L"Выберите комбинацию механик, целевую платформу и распределите фокус разработки", -1, &fontSmall, PointF(cx, cy + 26), &textMuted);

        float formY = cy + 52.0f;
        float formH = (float)rc.bottom - formY - 16.0f;
        FillGlassCard(g, cx, formY, cw, formH, 12, colCardTop, colCardBot, colCardBorder);

        g.DrawString(L"1. Название проекта:", -1, &fontBold, PointF(cx + 20, formY + 16), &textWhite);
        FillGlassCard(g, cx + 20, formY + 40, cw - 260, 42, 8, Color(255, 14, 18, 28), Color(255, 10, 14, 22), colCardBorder);
        SolidBrush bTitle(colAmber);
        g.DrawString(g_devTitle.c_str(), -1, &fontTitle, PointF(cx + 34, formY + 50), &bTitle);

        FillGlassCard(g, cx + cw - 225, formY + 40, 205, 42, 8, Color(255, 30, 38, 58), Color(255, 22, 28, 44), colIndigo);
        DrawVectorIcon(g, ICON_DICE, cx + cw - 215, formY + 49, 24, colWhite);
        g.DrawString(L"Случайное имя [Tab]", -1, &fontBold, PointF(cx + cw - 182, formY + 51), &textWhite);

        // Жанры
        g.DrawString(L"2. Жанр игры [Клавиши 1-6]:", -1, &fontBold, PointF(cx + 20, formY + 96), &textWhite);
        float gw = (cw - 60.0f) / 3.0f;
        for (size_t i = 0; i < g_genres.size(); i++) {
            float gx = cx + 20.0f + (i % 3) * (gw + 10.0f);
            float gy = formY + 122.0f + (i / 3) * 60.0f;
            bool isSel = ((int)i == g_devGenreIdx);

            if (isSel) {
                FillGlassCard(g, gx, gy, gw, 52, 8, Color(255, 99, 102, 241), Color(255, 79, 70, 229), colWhite);
            } else {
                FillGlassCard(g, gx, gy, gw, 52, 8, Color(255, 24, 30, 46), Color(255, 18, 22, 34), colCardBorder);
            }

            DrawVectorIcon(g, ICON_GAMEPAD, gx + 10, gy + 14, 24, isSel ? colWhite : colIndigo);
            std::wstring gNum = L"[" + std::to_wstring(i + 1) + L"] " + g_genres[i].name;
            SolidBrush bGName(colWhite);
            g.DrawString(gNum.c_str(), -1, &fontBold, PointF(gx + 40, gy + 8), &bGName);

            std::wstring cStr = L"Стоимость: $" + std::to_wstring(g_genres[i].cost);
            SolidBrush bCost(isSel ? Color(255, 220, 230, 255) : colMuted);
            g.DrawString(cStr.c_str(), -1, &fontMicro, PointF(gx + 40, gy + 28), &bCost);
        }

        // Сеттинг
        g.DrawString(L"3. Сеттинг / Тематика [Q, W, E, R, T, Y, U, I]:", -1, &fontBold, PointF(cx + 20, formY + 256), &textWhite);
        const wchar_t* thKeys[] = {L"[Q]", L"[W]", L"[E]", L"[R]", L"[T]", L"[Y]", L"[U]", L"[I]"};
        float tw = (cw - 70.0f) / 4.0f;
        for (size_t i = 0; i < (std::min)((size_t)8, g_themes.size()); i++) {
            float tx = cx + 20.0f + (i % 4) * (tw + 10.0f);
            float ty = formY + 282.0f + (i / 4) * 44.0f;
            bool isSel = ((int)i == g_devThemeIdx);

            if (isSel) {
                FillGlassCard(g, tx, ty, tw, 36, 6, Color(255, 16, 185, 129), Color(255, 5, 150, 105), colWhite);
            } else {
                FillGlassCard(g, tx, ty, tw, 36, 6, Color(255, 24, 30, 46), Color(255, 18, 22, 34), colCardBorder);
            }

            std::wstring thStr = std::wstring(thKeys[i]) + L" " + g_themes[i].name;
            SolidBrush bTh(isSel ? colWhite : colMuted);
            g.DrawString(thStr.c_str(), -1, &fontSmall, PointF(tx + 10, ty + 9), &bTh);
        }

        // Платформы
        g.DrawString(L"4. Платформа [Z, X, C, V, B]:", -1, &fontBold, PointF(cx + 20, formY + 382), &textWhite);
        const wchar_t* plKeys[] = {L"[Z]", L"[X]", L"[C]", L"[V]", L"[B]"};
        float pw = (cw - 60.0f) / 5.0f;
        for (size_t i = 0; i < (std::min)((size_t)5, g_platforms.size()); i++) {
            float px = cx + 20.0f + i * (pw + 10.0f);
            float py = formY + 408.0f;
            bool isSel = ((int)i == g_devPlatformIdx);

            if (isSel) {
                FillGlassCard(g, px, py, pw, 50, 8, Color(255, 6, 182, 212), Color(255, 8, 145, 178), colWhite);
            } else {
                FillGlassCard(g, px, py, pw, 50, 8, Color(255, 24, 30, 46), Color(255, 18, 22, 34), colCardBorder);
            }

            std::wstring pStr = std::wstring(plKeys[i]) + L" " + g_platforms[i].name;
            SolidBrush bP(colWhite);
            g.DrawString(pStr.c_str(), -1, &fontSmall, PointF(px + 8, py + 8), &bP);

            std::wstring pCost = L"$" + std::to_wstring(g_platforms[i].cost) + L" (x" + std::to_wstring((int)(g_platforms[i].audienceShare * 100)) + L"%)";
            SolidBrush bPCost(isSel ? Color(255, 220, 245, 255) : colCyan);
            g.DrawString(pCost.c_str(), -1, &fontMicro, PointF(px + 8, py + 28), &bPCost);
        }

        // Кнопка старта
        float btnStartY = formH - 64.0f;
        int totalDevCost = g_genres[g_devGenreIdx].cost + g_platforms[g_devPlatformIdx].cost;
        if (g_devScale == 1) totalDevCost = (int)(totalDevCost * 1.5);
        if (g_devScale == 2) totalDevCost *= 3;

        FillGlassCard(g, cx + 20, formY + btnStartY, cw - 40, 52, 10, colIndigo, Color(255, 79, 70, 229), colWhite);
        DrawVectorIcon(g, ICON_ROCKET, cx + cw / 2 - 180, formY + btnStartY + 14, 24, colWhite);
        std::wstring startTxt = L"НАЧАТЬ РАЗРАБОТКУ • Бюджет: $" + std::to_wstring(totalDevCost) + L" [ENTER]";
        g.DrawString(startTxt.c_str(), -1, &fontBig, PointF(cx + cw / 2 - 145, formY + btnStartY + 14), &textWhite);
    }

    // --- ВКЛАДКА 2: ПОРТФОЛИО ИГР ---
    else if (currentTab == TAB_PORTFOLIO) {
        g.DrawString(L"Портфолио выпущенных видеоигр", -1, &fontBig, PointF(cx, cy), &textWhite);
        g.DrawString(L"История успехов, тиражи продаж, рецензии прессы и финансовые отчеты", -1, &fontSmall, PointF(cx, cy + 26), &textMuted);

        if (g_games.empty()) {
            float emptyY = cy + 60.0f;
            FillGlassCard(g, cx, emptyY, cw, 220, 12, colCardTop, colCardBot, colCardBorder);
            DrawVectorIcon(g, ICON_GAMEPAD, cx + cw / 2 - 32, emptyY + 40, 64, colMuted);
            StringFormat sf;
            sf.SetAlignment(StringAlignmentCenter);
            g.DrawString(L"Вы пока не выпустили ни одной игры.", -1, &fontBold, RectF(cx, emptyY + 120, cw, 30), &sf, &textWhite);
            g.DrawString(L"Нажмите «Создать игру [N]», чтобы выпустить свой первый проект!", -1, &fontSmall, RectF(cx, emptyY + 150, cw, 30), &sf, &textMuted);
        } else {
            for (size_t i = 0; i < (std::min)((size_t)5, g_games.size()); i++) {
                float gy = cy + 56.0f + i * 108.0f;
                FillGlassCard(g, cx, gy, cw, 96, 10, colCardTop, colCardBot, colCardBorder);

                FillGlassCard(g, cx + 14, gy + 12, 72, 72, 8, colIndigo, Color(255, 79, 70, 229), colWhite);
                DrawVectorIcon(g, ICON_GAMEPAD, cx + 30, gy + 28, 40, colWhite);

                g.DrawString(g_games[i].title.c_str(), -1, &fontBig, PointF(cx + 100, gy + 14), &textWhite);
                std::wstring tags = g_games[i].genre + L" • " + g_games[i].theme + L" • " + g_games[i].platform + L" • " + g_games[i].engine;
                SolidBrush bTags(colPurple);
                g.DrawString(tags.c_str(), -1, &fontSmall, PointF(cx + 100, gy + 42), &bTags);

                std::wstringstream ssSales;
                ssSales << L"Продано копий: " << g_games[i].copiesSold << L" шт.   |   Выручка: +$" << g_games[i].revenue;
                SolidBrush bSales(colEmerald);
                g.DrawString(ssSales.str().c_str(), -1, &fontBold, PointF(cx + 100, gy + 66), &bSales);

                std::wstringstream ssSc;
                ssSc << std::fixed << std::setprecision(1) << g_games[i].score;
                Color scoreCol = g_games[i].score >= 8.5 ? colAmber : (g_games[i].score >= 7.0 ? colCyan : colMuted);
                FillGlassCard(g, cx + cw - 110, gy + 16, 92, 64, 8, Color(255, 26, 34, 52), Color(255, 18, 23, 36), scoreCol);
                DrawVectorIcon(g, ICON_STAR, cx + cw - 98, gy + 24, 18, scoreCol);
                SolidBrush bSc(scoreCol);
                g.DrawString(ssSc.str().c_str(), -1, &fontBig, PointF(cx + cw - 74, gy + 22), &bSc);
                g.DrawString(L"ОЦЕНКА", -1, &fontMicro, PointF(cx + cw - 88, gy + 50), &textMuted);
            }
        }
    }

    // --- ВКЛАДКА 3: ПЕРСОНАЛ ---
    else if (currentTab == TAB_STAFF) {
        g.DrawString(L"Персонал студии и Агентство найма", -1, &fontBig, PointF(cx, cy), &textWhite);
        g.DrawString(L"Обучайте действующих разработчиков и нанимайте новых специалистов", -1, &fontSmall, PointF(cx, cy + 26), &textMuted);

        float listY = cy + 56.0f;
        g.DrawString(L"Команда в штате:", -1, &fontBold, PointF(cx, listY), &textWhite);
        for (size_t i = 0; i < g_staff.size(); i++) {
            float sy = listY + 26.0f + i * 86.0f;
            FillGlassCard(g, cx, sy, cw, 76, 8, colCardTop, colCardBot, colCardBorder);

            Color avCol = (i == 0 ? colAmber : colCyan);
            FillRoundedRect(g, &SolidBrush(avCol), cx + 14, sy + 14, 48, 48, 8);
            DrawVectorIcon(g, ICON_USERS, cx + 22, sy + 22, 32, Color(255, 15, 20, 30));

            g.DrawString(g_staff[i].name.c_str(), -1, &fontBold, PointF(cx + 74, sy + 14), &textWhite);
            SolidBrush bRole(avCol);
            g.DrawString(g_staff[i].role.c_str(), -1, &fontSmall, PointF(cx + 74, sy + 34), &bRole);

            std::wstringstream ssSk;
            ssSk << L"Код: " << g_staff[i].code << L"  |  Арт: " << g_staff[i].design << L"  |  Звук: " << g_staff[i].sound;
            SolidBrush bSk(colWhite);
            g.DrawString(ssSk.str().c_str(), -1, &fontSmall, PointF(cx + 74, sy + 52), &bSk);

            FillGlassCard(g, cx + cw - 180, sy + 18, 164, 40, 6, Color(255, 30, 38, 58), Color(255, 22, 28, 44), colIndigo);
            DrawVectorIcon(g, ICON_RESEARCH, cx + cw - 172, sy + 26, 22, colWhite);
            g.DrawString(L"Обучить $1,500 [T]", -1, &fontBold, PointF(cx + cw - 144, sy + 28), &textWhite);
        }

        float candY = listY + 30.0f + g_staff.size() * 86.0f + 14.0f;
        g.DrawString(L"Доступные кандидаты в агентстве:", -1, &fontBold, PointF(cx, candY), &textWhite);

        for (size_t i = 0; i < (std::min)((size_t)3, g_candidates.size()); i++) {
            float cyPos = candY + 26.0f + i * 86.0f;
            FillGlassCard(g, cx, cyPos, cw, 76, 8, colCardTop, colCardBot, colCardBorder);

            FillRoundedRect(g, &SolidBrush(colPurple), cx + 14, cyPos + 14, 48, 48, 8);
            DrawVectorIcon(g, ICON_USERS, cx + 22, cyPos + 22, 32, Color(255, 15, 20, 30));

            g.DrawString(g_candidates[i].name.c_str(), -1, &fontBold, PointF(cx + 74, cyPos + 14), &textWhite);
            SolidBrush bRole(colPurple);
            g.DrawString(g_candidates[i].role.c_str(), -1, &fontSmall, PointF(cx + 74, cyPos + 34), &bRole);

            std::wstringstream ssSk;
            ssSk << L"Код: " << g_candidates[i].code << L"  |  Арт: " << g_candidates[i].design << L"  |  Звук: " << g_candidates[i].sound << L"  |  $" << g_candidates[i].salary << L"/мес";
            SolidBrush bSk(colWhite);
            g.DrawString(ssSk.str().c_str(), -1, &fontSmall, PointF(cx + 74, cyPos + 52), &bSk);

            bool canHire = (g_staff.size() < (size_t)g_offices[g_currentOfficeIdx].capacity && g_money >= g_candidates[i].hireCost);
            if (canHire) {
                FillGlassCard(g, cx + cw - 180, cyPos + 18, 164, 40, 6, colEmerald, Color(255, 5, 150, 105), colWhite);
            } else {
                FillGlassCard(g, cx + cw - 180, cyPos + 18, 164, 40, 6, Color(255, 30, 38, 58), Color(255, 22, 28, 44), colCardBorder);
            }
            DrawVectorIcon(g, ICON_PLUS, cx + cw - 172, cyPos + 26, 22, colWhite);
            std::wstring hTxt = L"Нанять $" + std::to_wstring(g_candidates[i].hireCost);
            g.DrawString(hTxt.c_str(), -1, &fontBold, PointF(cx + cw - 144, cyPos + 28), &textWhite);
        }
    }

    // --- ВКЛАДКА 4: ДВИЖКИ ---
    else if (currentTab == TAB_ENGINES) {
        g.DrawString(L"Конструктор Проприетарных Игровых Движков", -1, &fontBig, PointF(cx, cy), &textWhite);
        g.DrawString(L"Собственные технологии повышают множитель очков разработки и приносят роялти", -1, &fontSmall, PointF(cx, cy + 26), &textMuted);

        float engY = cy + 56.0f;
        for (size_t i = 0; i < g_engines.size(); i++) {
            float ey = engY + i * 116.0f;
            FillGlassCard(g, cx, ey, cw, 104, 10, colCardTop, colCardBot, colCardBorder);

            FillGlassCard(g, cx + 16, ey + 16, 68, 68, 8, colPurple, Color(255, 126, 34, 206), colWhite);
            DrawVectorIcon(g, ICON_GEAR, cx + 28, ey + 28, 44, colWhite);

            g.DrawString(g_engines[i].name.c_str(), -1, &fontBig, PointF(cx + 100, ey + 16), &textWhite);

            std::wstringstream ssMult;
            ssMult << L"Множитель очков разработки: x" << std::fixed << std::setprecision(2) << g_engines[i].mult;
            SolidBrush bMult(colEmerald);
            g.DrawString(ssMult.str().c_str(), -1, &fontBold, PointF(cx + 100, ey + 44), &bMult);

            std::wstring modStr = L"Встроенные модули: ";
            for (const auto& m : g_engines[i].modules) modStr += m + L", ";
            g.DrawString(modStr.c_str(), -1, &fontSmall, PointF(cx + 100, ey + 70), &textMuted);

            if (g_engines[i].isProprietary) {
                FillGlassCard(g, cx + cw - 260, ey + 24, 240, 48, 8, Color(255, 20, 36, 30), Color(255, 14, 28, 22), colEmerald);
                DrawVectorIcon(g, ICON_DOLLAR, cx + cw - 250, ey + 36, 24, colEmerald);
                g.DrawString(L"Роялти лицензий:", -1, &fontMicro, PointF(cx + cw - 220, ey + 28), &textMuted);
                g.DrawString(L"+$1,100 / месяц", -1, &fontBold, PointF(cx + cw - 220, ey + 46), &SolidBrush(colEmerald));
            }
        }

        float btnEy = engY + g_engines.size() * 116.0f + 16.0f;
        FillGlassCard(g, cx, btnEy, cw, 56, 10, colIndigo, Color(255, 79, 70, 229), colWhite);
        DrawVectorIcon(g, ICON_GEAR, cx + 24, btnEy + 16, 26, colWhite);
        g.DrawString(L"Собрать Titan NextGen Engine ($15,000) [Нажмите E]", -1, &fontBig, PointF(cx + 62, btnEy + 16), &textWhite);
    }

    // --- ВКЛАДКА 5: ИССЛЕДОВАНИЯ ---
    else if (currentTab == TAB_RESEARCH) {
        g.DrawString(L"Лаборатория исследований и патентов (R&D)", -1, &fontBig, PointF(cx, cy), &textWhite);
        std::wstring rpSub = L"Доступный баланс очков науки: " + std::to_wstring(g_rp) + L" RP";
        SolidBrush bCyanSub(colCyan);
        g.DrawString(rpSub.c_str(), -1, &fontBold, PointF(cx, cy + 26), &bCyanSub);

        float resY = cy + 56.0f;
        for (size_t i = 0; i < g_researches.size(); i++) {
            float ry = resY + i * 94.0f;
            FillGlassCard(g, cx, ry, cw, 82, 8, colCardTop, colCardBot, colCardBorder);

            DrawVectorIcon(g, g_researches[i].unlocked ? ICON_CHECK : ICON_RESEARCH, cx + 18, ry + 24, 32, g_researches[i].unlocked ? colEmerald : colCyan);

            g.DrawString(g_researches[i].title.c_str(), -1, &fontBold, PointF(cx + 64, ry + 16), &textWhite);
            g.DrawString(g_researches[i].desc.c_str(), -1, &fontSmall, PointF(cx + 64, ry + 42), &textMuted);

            if (g_researches[i].unlocked) {
                FillGlassCard(g, cx + cw - 160, ry + 20, 140, 42, 6, Color(255, 20, 36, 30), Color(255, 14, 28, 22), colEmerald);
                SolidBrush bDone(colEmerald);
                g.DrawString(L"ИЗУЧЕНО ✔", -1, &fontBold, PointF(cx + cw - 134, ry + 32), &bDone);
            } else {
                bool canBuy = (g_rp >= g_researches[i].rpCost);
                if (canBuy) {
                    FillGlassCard(g, cx + cw - 160, ry + 20, 140, 42, 6, colCyan, Color(255, 8, 145, 178), colWhite);
                } else {
                    FillGlassCard(g, cx + cw - 160, ry + 20, 140, 42, 6, Color(255, 30, 38, 58), Color(255, 22, 28, 44), colCardBorder);
                }
                std::wstring rpBtn = L"Изучить (" + std::to_wstring(g_researches[i].rpCost) + L" RP)";
                g.DrawString(rpBtn.c_str(), -1, &fontBold, PointF(cx + cw - 150, ry + 32), &textWhite);
            }
        }
    }

    // --- ВКЛАДКА 6: УЛУЧШЕНИЯ ОФИСА ---
    else if (currentTab == TAB_UPGRADES) {
        g.DrawString(L"Недвижимость и Расширение студии", -1, &fontBig, PointF(cx, cy), &textWhite);
        g.DrawString(L"Переезжайте в более просторные офисы для найма дополнительных специалистов", -1, &fontSmall, PointF(cx, cy + 26), &textMuted);

        float offY = cy + 56.0f;
        for (size_t i = 0; i < g_offices.size(); i++) {
            float oy = offY + i * 114.0f;
            bool isCurrent = ((int)i == g_currentOfficeIdx);

            if (isCurrent) {
                FillGlassCard(g, cx, oy, cw, 102, 10, Color(255, 24, 38, 58), Color(255, 18, 28, 44), colIndigo);
            } else {
                FillGlassCard(g, cx, oy, cw, 102, 10, colCardTop, colCardBot, colCardBorder);
            }

            FillGlassCard(g, cx + 16, oy + 16, 68, 68, 8, isCurrent ? colIndigo : Color(255, 35, 45, 68), Color(255, 20, 26, 40), colWhite);
            DrawVectorIcon(g, ICON_OFFICE, cx + 28, oy + 28, 44, colWhite);

            g.DrawString(g_offices[i].name.c_str(), -1, &fontBig, PointF(cx + 100, oy + 16), &textWhite);
            g.DrawString(g_offices[i].desc.c_str(), -1, &fontSmall, PointF(cx + 100, oy + 42), &textMuted);

            std::wstringstream ssInf;
            ssInf << L"Вместимость: " << g_offices[i].capacity << L" чел.   |   Аренда: $" << g_offices[i].rent << L"/мес";
            SolidBrush bInf(colCyan);
            g.DrawString(ssInf.str().c_str(), -1, &fontBold, PointF(cx + 100, oy + 68), &bInf);

            if (isCurrent) {
                FillGlassCard(g, cx + cw - 180, oy + 30, 160, 42, 6, Color(255, 20, 36, 30), Color(255, 14, 28, 22), colEmerald);
                SolidBrush bCur(colEmerald);
                g.DrawString(L"ТЕКУЩИЙ ОФИС ✔", -1, &fontBold, PointF(cx + cw - 165, oy + 42), &bCur);
            } else if ((int)i == g_currentOfficeIdx + 1) {
                bool canAfford = (g_money >= g_offices[i].price);
                if (canAfford) {
                    FillGlassCard(g, cx + cw - 180, oy + 30, 160, 42, 6, colEmerald, Color(255, 5, 150, 105), colWhite);
                } else {
                    FillGlassCard(g, cx + cw - 180, oy + 30, 160, 42, 6, Color(255, 30, 38, 58), Color(255, 22, 28, 44), colCardBorder);
                }
                std::wstring prStr = L"Купить $" + std::to_wstring(g_offices[i].price);
                g.DrawString(prStr.c_str(), -1, &fontBold, PointF(cx + cw - 165, oy + 42), &textWhite);
            }
        }
    }

    // --- ВКЛАДКА 7: ДОСТИЖЕНИЯ ---
    else if (currentTab == TAB_ACHIEVEMENTS) {
        g.DrawString(L"Достижения и Награды студии", -1, &fontBig, PointF(cx, cy), &textWhite);
        g.DrawString(L"Выполняйте условия испытаний для получения денежных бонусов и очков науки", -1, &fontSmall, PointF(cx, cy + 26), &textMuted);

        float achY = cy + 56.0f;
        for (size_t i = 0; i < g_achievements.size(); i++) {
            float ay = achY + i * 94.0f;
            FillGlassCard(g, cx, ay, cw, 82, 8, colCardTop, colCardBot, colCardBorder);

            DrawVectorIcon(g, g_achievements[i].unlocked ? ICON_TROPHY : ICON_LOCK, cx + 18, ay + 24, 32, g_achievements[i].unlocked ? colAmber : colMuted);

            g.DrawString(g_achievements[i].title.c_str(), -1, &fontBold, PointF(cx + 64, ay + 16), g_achievements[i].unlocked ? &SolidBrush(colAmber) : &textWhite);
            g.DrawString(g_achievements[i].desc.c_str(), -1, &fontSmall, PointF(cx + 64, ay + 42), &textMuted);

            std::wstringstream ssR;
            ssR << L"Награда: +$" << g_achievements[i].rewardCash << L" | +" << g_achievements[i].rewardRp << L" RP";
            SolidBrush bRew(colEmerald);
            g.DrawString(ssR.str().c_str(), -1, &fontBold, PointF(cx + 420, ay + 30), &bRew);

            if (g_achievements[i].unlocked) {
                FillGlassCard(g, cx + cw - 160, ay + 20, 140, 42, 6, Color(255, 45, 36, 16), Color(255, 30, 24, 10), colAmber);
                SolidBrush bDone(colAmber);
                g.DrawString(L"ВЫПОЛНЕНО ★", -1, &fontBold, PointF(cx + cw - 146, ay + 32), &bDone);
            } else {
                FillGlassCard(g, cx + cw - 160, ay + 20, 140, 42, 6, Color(255, 24, 30, 44), Color(255, 18, 22, 34), colCardBorder);
                g.DrawString(L"В ПРОЦЕССЕ 🔒", -1, &fontSmall, PointF(cx + cw - 146, ay + 32), &textMuted);
            }
        }
    }

    // ==========================================
    // 4. МОДАЛЬНОЕ ОКНО РЕЦЕНЗИЙ ПРЕССЫ
    // ==========================================
    if (g_showReviewDialog) {
        SolidBrush modalDark(Color(220, 6, 8, 14));
        g.FillRectangle(&modalDark, 0, 0, rc.right, rc.bottom);

        float mw = 640.0f;
        float mh = 500.0f;
        float mx = ((float)rc.right - mw) / 2.0f;
        float my = ((float)rc.bottom - mh) / 2.0f;

        FillGlassCard(g, mx, my, mw, mh, 16, Color(255, 26, 34, 52), Color(255, 17, 22, 36), colIndigo);

        DrawVectorIcon(g, ICON_TROPHY, mx + mw / 2 - 24, my + 24, 48, colAmber);
        StringFormat sf;
        sf.SetAlignment(StringAlignmentCenter);
        g.DrawString(L"РЕЦЕНЗИИ МИРОВОЙ ПРЕССЫ!", -1, &fontBig, RectF(mx, my + 80, mw, 30), &sf, &SolidBrush(colAmber));
        g.DrawString(g_lastReviewedGame.title.c_str(), -1, &fontTitle, RectF(mx, my + 110, mw, 30), &sf, &textWhite);

        std::wstringstream ssFin;
        ssFin << std::fixed << std::setprecision(1) << g_lastReviewedGame.score << L" / 10";
        SolidBrush bHuge(colEmerald);
        g.DrawString(ssFin.str().c_str(), -1, &fontHuge, RectF(mx, my + 140, mw, 40), &sf, &bHuge);

        for (size_t i = 0; i < g_lastReviewScores.size(); i++) {
            float ry = my + 196.0f + i * 50.0f;
            FillGlassCard(g, mx + 40, ry, mw - 80, 42, 8, Color(255, 20, 26, 42), Color(255, 14, 18, 30), colCardBorder);
            g.DrawString(g_lastReviewScores[i].first.c_str(), -1, &fontBold, PointF(mx + 60, ry + 12), &textWhite);

            std::wstringstream ssSc;
            ssSc << std::fixed << std::setprecision(1) << g_lastReviewScores[i].second;
            SolidBrush bS(g_lastReviewScores[i].second >= 8.0 ? colAmber : colCyan);
            g.DrawString(ssSc.str().c_str(), -1, &fontBold, PointF(mx + mw - 120, ry + 12), &bS);
        }

        FillGlassCard(g, mx + 100, my + mh - 66, mw - 200, 48, 10, colEmerald, Color(255, 5, 150, 105), colWhite);
        g.DrawString(L"НАЧАТЬ ПРОДАЖИ! [ENTER / КЛИК]", -1, &fontBold, RectF(mx + 100, my + mh - 54, mw - 200, 30), &sf, &textWhite);
    }

    // ==========================================
    // 5. МОДАЛЬНОЕ ОКНО ОХОТЫ НА БАГИ
    // ==========================================
    if (g_showBugHuntDialog) {
        SolidBrush modalDark(Color(230, 8, 10, 18));
        g.FillRectangle(&modalDark, 0, 0, rc.right, rc.bottom);

        float mw = 720.0f;
        float mh = 520.0f;
        float mx = ((float)rc.right - mw) / 2.0f;
        float my = ((float)rc.bottom - mh) / 2.0f;

        FillGlassCard(g, mx, my, mw, mh, 16, Color(255, 28, 20, 26), Color(255, 18, 14, 20), colRose);

        DrawVectorIcon(g, ICON_BUG, mx + 30, my + 20, 36, colRose);
        g.DrawString(L"ОХОТА НА БАГИ! КЛИКАЙТЕ ПО ЖУКАМ!", -1, &fontBig, PointF(mx + 76, my + 24), &SolidBrush(colRose));

        std::wstringstream ssTimer;
        ssTimer << L"Таймер: " << g_bugHuntTimer << L"с   |   Уничтожено: " << g_bugsSquashed << L" багов";
        g.DrawString(ssTimer.str().c_str(), -1, &fontBold, PointF(mx + mw - 320, my + 28), &textWhite);

        FillGlassCard(g, mx + 30, my + 70, mw - 60, mh - 150, 12, Color(255, 14, 16, 24), Color(255, 10, 12, 18), colCardBorder);

        for (const auto& b : g_huntBugs) {
            if (b.alive) {
                float bx = mx + 30 + b.x;
                float by = my + 70 + b.y;
                FillRoundedRect(g, &SolidBrush(Color(255, 239, 68, 68)), bx, by, b.size, b.size, 8);
                DrawVectorIcon(g, ICON_BUG, bx + 5, by + 5, b.size - 10, colWhite);
            }
        }

        FillGlassCard(g, mx + mw / 2 - 120, my + mh - 60, 240, 44, 8, Color(255, 30, 38, 58), Color(255, 22, 28, 44), colCardBorder);
        StringFormat sf;
        sf.SetAlignment(StringAlignmentCenter);
        g.DrawString(L"ЗАВЕРШИТЬ ОХОТУ [ESC]", -1, &fontBold, RectF(mx + mw / 2 - 120, my + mh - 48, 240, 30), &sf, &textWhite);
    }
}

// Обработка кликов мыши
void HandleMouseClick(int x, int y, HWND hwnd) {
    if (g_showReviewDialog) {
        float mw = 640.0f;
        float mh = 500.0f;
        float mx = (WINDOW_WIDTH - mw) / 2.0f;
        float my = (WINDOW_HEIGHT - mh) / 2.0f;
        if (x >= mx + 100 && x <= mx + mw - 100 && y >= my + mh - 66 && y <= my + mh - 18) {
            g_showReviewDialog = false;
            currentTab = TAB_PORTFOLIO;
            InvalidateRect(hwnd, NULL, FALSE);
        }
        return;
    }

    if (g_showBugHuntDialog) {
        float mw = 720.0f;
        float mh = 520.0f;
        float mx = (WINDOW_WIDTH - mw) / 2.0f;
        float my = (WINDOW_HEIGHT - mh) / 2.0f;

        for (auto& b : g_huntBugs) {
            if (b.alive) {
                float bx = mx + 30 + b.x;
                float by = my + 70 + b.y;
                if (x >= bx && x <= bx + b.size && y >= by && y <= by + b.size) {
                    b.alive = false;
                    g_bugsSquashed++;
                    g_devPtsBugs = (std::max)(0, g_devPtsBugs - 1);
                    PlaySoundBeep(950, 35);
                    InvalidateRect(hwnd, NULL, FALSE);
                    return;
                }
            }
        }

        if (x >= mx + mw / 2 - 120 && x <= mx + mw / 2 + 120 && y >= my + mh - 60 && y <= my + mh - 16) {
            g_showBugHuntDialog = false;
            InvalidateRect(hwnd, NULL, FALSE);
        }
        return;
    }

    // Кнопки скорости
    if (y >= 20 && y <= 54) {
        float spX = 1070.0f;
        for (int i = 0; i < 4; i++) {
            float bx = spX + 8 + i * 53;
            if (x >= bx && x <= bx + 48) {
                int spds[4] = {0, 1, 2, 5};
                g_speed = spds[i];
                PlaySoundBeep(700, 30);
                InvalidateRect(hwnd, NULL, FALSE);
                return;
            }
        }
    }

    // Сайдбар меню
    float topH = 74.0f;
    if (x >= 12 && x <= 203 && y >= topH + 16 && y <= topH + 16 + 8 * 46) {
        int idx = (int)((y - (topH + 16)) / 46);
        if (idx >= 0 && idx < 8) {
            currentTab = (TabIndex)idx;
            PlaySoundBeep(600, 25);
            InvalidateRect(hwnd, NULL, FALSE);
        }
        return;
    }

    // Быстрый дев [N]
    if (x >= 12 && x <= 203 && y >= WINDOW_HEIGHT - 105 && y <= WINDOW_HEIGHT - 63) {
        currentTab = TAB_DEV_WIZARD;
        PlaySoundBeep(700, 30);
        InvalidateRect(hwnd, NULL, FALSE);
        return;
    }

    // Быстрый фриланс [F]
    if (x >= 12 && x <= 203 && y >= WINDOW_HEIGHT - 55 && y <= WINDOW_HEIGHT - 15) {
        g_money += 3000;
        g_feedLogs.insert(g_feedLogs.begin(), L"💼 Выполнен контрактный фриланс: +$3,000 в кассу студии!");
        PlaySoundBeep(850, 40);
        InvalidateRect(hwnd, NULL, FALSE);
        return;
    }

    float sideW = 215.0f;
    float cx = sideW + 20.0f;
    float cw = (float)WINDOW_WIDTH - cx - 20.0f;

    // Вкладка 0: Офис
    if (currentTab == TAB_OFFICE) {
        if (g_isDevActive) {
            float roomY = topH + 16.0f + 52.0f;
            float devY = roomY + 300.0f + 14.0f;
            if (x >= cx + 18 && x <= cx + 198 && y >= devY + 70 && y <= devY + 106) {
                StartBugHunt();
                InvalidateRect(hwnd, NULL, FALSE);
                return;
            }
            if (x >= cx + 210 && x <= cx + 380 && y >= devY + 70 && y <= devY + 106) {
                g_isCrunch = !g_isCrunch;
                PlaySoundBeep(g_isCrunch ? 1100 : 450, 40);
                InvalidateRect(hwnd, NULL, FALSE);
                return;
            }
            if (x >= cx + cw - 240 && x <= cx + cw - 18 && y >= devY + 70 && y <= devY + 106) {
                if (g_devProgress >= 100.0) {
                    FinishDevelopment();
                    InvalidateRect(hwnd, NULL, FALSE);
                    return;
                }
            }
        }
    }

    // Вкладка 1: Визард
    else if (currentTab == TAB_DEV_WIZARD) {
        float formY = topH + 16.0f + 52.0f;
        if (x >= cx + cw - 225 && x <= cx + cw - 20 && y >= formY + 40 && y <= formY + 82) {
            g_devTitle = g_randomTitles[rand() % g_randomTitles.size()];
            PlaySoundBeep(800, 30);
            InvalidateRect(hwnd, NULL, FALSE);
            return;
        }

        float gw = (cw - 60.0f) / 3.0f;
        for (size_t i = 0; i < g_genres.size(); i++) {
            float gx = cx + 20.0f + (i % 3) * (gw + 10.0f);
            float gy = formY + 122.0f + (i / 3) * 60.0f;
            if (x >= gx && x <= gx + gw && y >= gy && y <= gy + 52) {
                g_devGenreIdx = (int)i;
                PlaySoundBeep(650, 25);
                InvalidateRect(hwnd, NULL, FALSE);
                return;
            }
        }

        float tw = (cw - 70.0f) / 4.0f;
        for (size_t i = 0; i < (std::min)((size_t)8, g_themes.size()); i++) {
            float tx = cx + 20.0f + (i % 4) * (tw + 10.0f);
            float ty = formY + 282.0f + (i / 4) * 44.0f;
            if (x >= tx && x <= tx + tw && y >= ty && y <= ty + 36) {
                g_devThemeIdx = (int)i;
                PlaySoundBeep(700, 25);
                InvalidateRect(hwnd, NULL, FALSE);
                return;
            }
        }

        float pw = (cw - 60.0f) / 5.0f;
        for (size_t i = 0; i < (std::min)((size_t)5, g_platforms.size()); i++) {
            float px = cx + 20.0f + i * (pw + 10.0f);
            float py = formY + 408.0f;
            if (x >= px && x <= px + pw && y >= py && y <= py + 50) {
                g_devPlatformIdx = (int)i;
                PlaySoundBeep(750, 25);
                InvalidateRect(hwnd, NULL, FALSE);
                return;
            }
        }

        float formH = (float)WINDOW_HEIGHT - formY - 16.0f;
        float btnStartY = formH - 64.0f;
        if (x >= cx + 20 && x <= cx + cw - 20 && y >= formY + btnStartY && y <= formY + btnStartY + 52) {
            StartDevelopment();
            InvalidateRect(hwnd, NULL, FALSE);
            return;
        }
    }

    // Вкладка 3: Персонал
    else if (currentTab == TAB_STAFF) {
        float listY = topH + 16.0f + 56.0f;
        for (size_t i = 0; i < g_staff.size(); i++) {
            float sy = listY + 26.0f + i * 86.0f;
            if (x >= cx + cw - 180 && x <= cx + cw - 16 && y >= sy + 18 && y <= sy + 58) {
                if (g_money >= 1500) {
                    g_money -= 1500;
                    g_staff[i].code += 4;
                    g_staff[i].design += 4;
                    g_staff[i].sound += 3;
                    g_studioRating += 2000;
                    g_feedLogs.insert(g_feedLogs.begin(), L"🎓 " + g_staff[i].name + L" завершил обучение (+4 Код, +4 Арт, +3 Звук)!");
                    PlaySoundBeep(1000, 50);
                    CheckStudioRating();
                    InvalidateRect(hwnd, NULL, FALSE);
                    return;
                }
            }
        }

        float candY = listY + 30.0f + g_staff.size() * 86.0f + 14.0f;
        for (size_t i = 0; i < (std::min)((size_t)3, g_candidates.size()); i++) {
            float cyPos = candY + 26.0f + i * 86.0f;
            if (x >= cx + cw - 180 && x <= cx + cw - 16 && y >= cyPos + 18 && y <= cyPos + 58) {
                if (g_staff.size() < (size_t)g_offices[g_currentOfficeIdx].capacity && g_money >= g_candidates[i].hireCost) {
                    g_money -= g_candidates[i].hireCost;
                    Employee emp = {
                        g_candidates[i].id,
                        g_candidates[i].name,
                        g_candidates[i].role,
                        g_candidates[i].code,
                        g_candidates[i].design,
                        g_candidates[i].sound,
                        g_candidates[i].salary,
                        100,
                        g_candidates[i].avatarColorIdx
                    };
                    g_staff.push_back(emp);
                    g_studioRating += 10000;
                    g_feedLogs.insert(g_feedLogs.begin(), L"🎉 В команду нанят новый специалист: " + emp.name + L" (" + emp.role + L")!");
                    g_candidates.erase(g_candidates.begin() + i);
                    PlaySoundBeep(1100, 60);
                    CheckStudioRating();
                    InvalidateRect(hwnd, NULL, FALSE);
                    return;
                }
            }
        }
    }

    // Вкладка 4: Движки
    else if (currentTab == TAB_ENGINES) {
        float engY = topH + 16.0f + 56.0f;
        float btnEy = engY + g_engines.size() * 116.0f + 16.0f;
        if (x >= cx && x <= cx + cw && y >= btnEy && y <= btnEy + 56) {
            if (g_money >= 15000) {
                g_money -= 15000;
                CustomEngine eng;
                eng.id = "titan_rtx";
                eng.name = L"Titan RTX RayTracing NextGen";
                eng.mult = 1.95;
                eng.modules = {L"Рэйтрейсинг v2", L"PhysX 5", L"DLSS 4", L"Пространственный звук"};
                eng.isProprietary = true;
                g_engines.push_back(eng);
                g_studioRating += 75000;
                g_innovationIndex += 25;
                g_feedLogs.insert(g_feedLogs.begin(), L"⚙️ Собран и запатентован флагманский движок Titan RTX! Рейтинг +75,000!");
                PlaySoundBeep(1200, 70);
                CheckStudioRating();
                InvalidateRect(hwnd, NULL, FALSE);
                return;
            }
        }
    }

    // Вкладка 5: Исследования
    else if (currentTab == TAB_RESEARCH) {
        float resY = topH + 16.0f + 56.0f;
        for (size_t i = 0; i < g_researches.size(); i++) {
            float ry = resY + i * 94.0f;
            if (!g_researches[i].unlocked && x >= cx + cw - 160 && x <= cx + cw - 20 && y >= ry + 20 && y <= ry + 62) {
                if (g_rp >= g_researches[i].rpCost) {
                    g_rp -= g_researches[i].rpCost;
                    g_researches[i].unlocked = true;
                    g_studioRating += 25000;
                    g_innovationIndex += 15;
                    g_feedLogs.insert(g_feedLogs.begin(), L"🔬 Завершено исследование: «" + g_researches[i].title + L"»! Рейтинг +25,000!");
                    PlaySoundBeep(1050, 60);
                    CheckStudioRating();
                    InvalidateRect(hwnd, NULL, FALSE);
                    return;
                }
            }
        }
    }

    // Вкладка 6: Улучшения офиса
    else if (currentTab == TAB_UPGRADES) {
        float offY = topH + 16.0f + 56.0f;
        for (size_t i = 0; i < g_offices.size(); i++) {
            float oy = offY + i * 114.0f;
            if ((int)i == g_currentOfficeIdx + 1 && x >= cx + cw - 180 && x <= cx + cw - 20 && y >= oy + 30 && y <= oy + 72) {
                if (g_money >= g_offices[i].price) {
                    g_money -= g_offices[i].price;
                    g_currentOfficeIdx = (int)i;
                    g_studioRating += 150000;
                    g_feedLogs.insert(g_feedLogs.begin(), L"🏢 Студия переехала в новый офис: «" + g_offices[i].name + L"»! Рейтинг +150,000!");
                    PlaySoundBeep(1200, 80);
                    CheckStudioRating();
                    CheckAchievements();
                    InvalidateRect(hwnd, NULL, FALSE);
                    return;
                }
            }
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
        case 'P': g_speed = (g_speed == 0 ? 1 : 0); break;
        case '1':
            if (currentTab == TAB_DEV_WIZARD) g_devGenreIdx = 0; else g_speed = 1;
            break;
        case '2':
            if (currentTab == TAB_DEV_WIZARD) g_devGenreIdx = 1; else g_speed = 2;
            break;
        case '3':
            if (currentTab == TAB_DEV_WIZARD) g_devGenreIdx = 2; else g_speed = 5;
            break;
        case '4': if (currentTab == TAB_DEV_WIZARD) g_devGenreIdx = 3; break;
        case '5': if (currentTab == TAB_DEV_WIZARD) g_devGenreIdx = 4; break;
        case '6': if (currentTab == TAB_DEV_WIZARD) g_devGenreIdx = 5; break;
        case 'Q': g_devThemeIdx = 0; break;
        case 'W': g_devThemeIdx = 1; break;
        case 'E':
            if (currentTab == TAB_ENGINES) {
                if (g_money >= 15000) {
                    g_money -= 15000;
                    CustomEngine eng;
                    eng.id = "titan_rtx";
                    eng.name = L"Titan RTX RayTracing NextGen";
                    eng.mult = 1.95;
                    eng.modules = {L"Рэйтрейсинг v2", L"PhysX 5", L"DLSS 4", L"Пространственный звук"};
                    eng.isProprietary = true;
                    g_engines.push_back(eng);
                    g_studioRating += 75000;
                    g_innovationIndex += 25;
                    g_feedLogs.insert(g_feedLogs.begin(), L"⚙️ Собран и запатентован флагманский движок Titan RTX! Рейтинг +75,000!");
                    PlaySoundBeep(1200, 70);
                    CheckStudioRating();
                }
            } else {
                g_devThemeIdx = 2;
            }
            break;
        case 'R':
            if (g_isDevActive && g_devProgress >= 100.0) FinishDevelopment(); else g_devThemeIdx = 3;
            break;
        case 'T':
            if (currentTab == TAB_STAFF && !g_staff.empty()) {
                if (g_money >= 1500) {
                    g_money -= 1500;
                    g_staff[0].code += 4;
                    g_staff[0].design += 4;
                    g_staff[0].sound += 3;
                    g_studioRating += 2000;
                    g_feedLogs.insert(g_feedLogs.begin(), L"🎓 " + g_staff[0].name + L" прошел курс обучения (+4 Код, +4 Арт, +3 Звук)!");
                    PlaySoundBeep(1000, 50);
                    CheckStudioRating();
                }
            } else {
                g_devThemeIdx = 4;
            }
            break;
        case 'Y': g_devThemeIdx = 5; break;
        case 'U': g_devThemeIdx = 6; break;
        case 'I': g_devThemeIdx = 7; break;
        case 'Z': g_devPlatformIdx = 0; break;
        case 'X': g_devPlatformIdx = 1; break;
        case 'C':
            if (g_isDevActive) {
                g_isCrunch = !g_isCrunch;
                PlaySoundBeep(g_isCrunch ? 1100 : 450, 40);
            } else {
                g_devPlatformIdx = 2;
            }
            break;
        case 'V': g_devPlatformIdx = 3; break;
        case 'B':
            if (g_isDevActive) StartBugHunt(); else g_devPlatformIdx = 4;
            break;
        case 'N': currentTab = TAB_DEV_WIZARD; break;
        case 'F':
            g_money += 3000;
            g_feedLogs.insert(g_feedLogs.begin(), L"💼 Выполнен контрактный фриланс: +$3,000 в кассу студии!");
            PlaySoundBeep(850, 40);
            break;
        case VK_TAB:
            if (currentTab == TAB_DEV_WIZARD) {
                g_devTitle = g_randomTitles[rand() % g_randomTitles.size()];
                PlaySoundBeep(800, 30);
            }
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
        case WM_ERASEBKGND:
            return 1;
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
