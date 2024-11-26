#include <Adafruit_GFX.h>  // Graphics library
#include <MCUFRIEND_kbv.h> // TFT driver
#include <TouchScreen.h>   // Touchscreen library

MCUFRIEND_kbv tft;

// Screen dimensions
#define SCREEN_WIDTH 320
#define SCREEN_HEIGHT 240

// Colors
#define BLACK   0x0000
#define WHITE   0xFFFF
#define BLUE    0x001F
#define GREEN   0x07E0
#define RED     0xF800
#define YELLOW  0xFFE0

// Touchscreen pins
#define YP A3  // Must be an analog pin
#define XM A2  // Must be an analog pin
#define YM 9   // Can be a digital pin
#define XP 8   // Can be a digital pin

// Screen touch calibration values (modify these for your screen)
#define TS_MINX 100
#define TS_MAXX 900
#define TS_MINY 100
#define TS_MAXY 900

TouchScreen ts = TouchScreen(XP, YP, XM, YM, 300); // 300 is the resistance of the touchscreen

void setup() {
    Serial.begin(9600);

    uint16_t ID = tft.readID();
    if (ID == 0xD3D3) ID = 0x9481; // Fallback for certain shields
    tft.begin(ID);

    // Show the initial screen
    showStartupPage();
}

void loop() {
    // Check for touchscreen input
    TSPoint p = ts.getPoint();
    if (p.z > 50 && p.z < 1000) { // Valid touch detected
        // Map touch coordinates to screen dimensions
        int touchX = map(p.x, TS_MINX, TS_MAXX, 0, SCREEN_WIDTH);
        int touchY = map(p.y, TS_MINY, TS_MAXY, 0, SCREEN_HEIGHT);

        // Check if touch is within button area
        if (touchX >= 100 && touchX <= 220 && touchY >= 180 && touchY <= 220) {
            drawLoadingScreen();
        }
    }
}

void showStartupPage() {
    // Clear the screen
    tft.fillScreen(BLACK);

    // Display "CoffeeOnDemand"
    tft.setTextColor(WHITE);
    tft.setTextSize(3);
    tft.setCursor(40, 100); // Adjust position as needed
    tft.print("CoffeeOnDemand");

    // Draw touch button
    tft.fillRect(100, 180, 120, 40, BLUE);  // Button rectangle
    tft.setTextColor(WHITE);
    tft.setTextSize(2);
    tft.setCursor(110, 190); // Center text inside button
    tft.print("Start");
}

void drawLoadingScreen() {
    // Clear the screen
    tft.fillScreen(BLACK);

    // Draw loading message
    tft.setTextColor(WHITE);
    tft.setTextSize(2);
    tft.setCursor(50, 50);
    tft.print("Loading...");

    // Draw an empty progress bar
    int progressBarX = 40;
    int progressBarY = 120;
    int progressBarWidth = 240;
    int progressBarHeight = 20;
    tft.drawRect(progressBarX, progressBarY, progressBarWidth, progressBarHeight, WHITE);

    // Simulate loading progress
    for (int i = 0; i <= 100; i++) {
        // Fill the progress bar
        int filledWidth = (i * progressBarWidth) / 100;
        tft.fillRect(progressBarX, progressBarY, filledWidth, progressBarHeight, BLUE);

        // Display the percentage
        tft.setTextColor(WHITE, BLACK); // Overwrite previous text
        tft.setCursor(140, 150);
        tft.print(i);
        tft.print("%");

        delay(50); // Simulate processing delay
    }

    // Indicate loading complete
    tft.fillScreen(GREEN);
    tft.setCursor(50, 100);
    tft.setTextColor(BLACK);
    tft.print("Loading Complete!");
}
