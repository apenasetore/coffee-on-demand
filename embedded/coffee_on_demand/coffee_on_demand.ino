#include <SPI.h>              
#include <Adafruit_GFX.h>                                                      // hardware-specific library
#include <MCUFRIEND_kbv.h>                                                     // hardware-specific library
#include "qrcode.h"
#include <TouchScreen.h>
#include <Fonts/FreeSans9pt7b.h>


// TFT LCD instance
MCUFRIEND_kbv tft;


// Touchscreen definitions
#define MINPRESSURE 200
#define MAXPRESSURE 1000
const int XP=8,XM=A2,YP=A3,YM=9;
const int TS_LEFT=120,TS_RT=903,TS_TOP=930,TS_BOT=54;
TouchScreen ts = TouchScreen(XP, YP, XM, YM, 300);

uint16_t rgb888ToRgb565(uint32_t color) {
    uint8_t r = (color >> 16) & 0xFF;
    uint8_t g = (color >> 8) & 0xFF;
    uint8_t b = color & 0xFF;
    return ((r >> 3) << 11) | ((g >> 2) << 5) | (b >> 3);
}

// some principal color definitions
// RGB 565 color picker at https://ee-programming-notepad.blogspot.com/2016/10/16-bit-color-generator-picker.html
#define WHITE       0xFFFF
#define BLACK       0x0000
#define RED         0xF800
#define GREEN       0x0f0f
#define COFFEE_ON_DEMAND_1  rgb888ToRgb565(0x717C89)
#define COFFEE_ON_DEMAND_2  rgb888ToRgb565(0x420217)


const unsigned char coffee_bean [] PROGMEM = {0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 
0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 
0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 
0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 
0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 
0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x0f, 0xff, 0xc0, 0x00, 0x00, 
0x00, 0x00, 0x00, 0x00, 0x00, 0x0f, 0xff, 0xc0, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x1f, 
0xff, 0xe0, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x7f, 0xff, 0xff, 0xc0, 0x00, 0x00, 0x00, 
0x00, 0x00, 0x00, 0x7f, 0xff, 0xff, 0xc0, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x7f, 0xff, 0xff, 
0xfe, 0x03, 0xff, 0xf0, 0x00, 0x00, 0x00, 0x7f, 0xff, 0xff, 0xfe, 0x07, 0xff, 0xf0, 0x00, 0x00, 
0x00, 0x1f, 0xff, 0xff, 0xf8, 0x07, 0xfe, 0x00, 0x00, 0x00, 0x03, 0x8f, 0xff, 0xff, 0xf8, 0xff, 
0xfe, 0x06, 0x00, 0x00, 0x03, 0x8f, 0xff, 0xff, 0xf8, 0xff, 0xfe, 0x06, 0x00, 0x00, 0x03, 0xe0, 
0x1f, 0xff, 0xc1, 0xff, 0xf8, 0xff, 0x80, 0x00, 0x03, 0xe0, 0x1f, 0xff, 0xc7, 0xff, 0xf0, 0xff, 
0x80, 0x00, 0x03, 0xf0, 0x00, 0x07, 0x07, 0xff, 0xf0, 0xff, 0x80, 0x00, 0x03, 0xff, 0xe0, 0x03, 
0x1f, 0xff, 0xf0, 0xff, 0x80, 0x00, 0x03, 0xff, 0xe0, 0x03, 0x1f, 0xff, 0xf0, 0xff, 0x80, 0x00, 
0x03, 0xff, 0xff, 0xf8, 0x3f, 0xff, 0xc7, 0xff, 0x80, 0x00, 0x03, 0xff, 0xff, 0xf8, 0xff, 0xff, 
0xc7, 0xff, 0x80, 0x00, 0x03, 0xff, 0xff, 0xf8, 0xff, 0xff, 0xc7, 0xff, 0x80, 0x00, 0x00, 0x7f, 
0xff, 0xf8, 0xff, 0xfe, 0x3f, 0xff, 0x80, 0x00, 0x00, 0x7f, 0xff, 0xf8, 0xff, 0xfe, 0x3f, 0xff, 
0x80, 0x00, 0x00, 0x7f, 0xff, 0xf8, 0xff, 0xfe, 0x3f, 0xff, 0x80, 0x00, 0x00, 0x7f, 0xff, 0xf8, 
0xff, 0xfe, 0x3f, 0xff, 0x80, 0x00, 0x00, 0x7f, 0xff, 0xf8, 0xff, 0xfe, 0x3f, 0xff, 0x80, 0x00, 
0x00, 0x1f, 0xff, 0xf8, 0xff, 0xfe, 0x3f, 0xff, 0x80, 0x00, 0x00, 0x0f, 0xff, 0xf8, 0xff, 0xfe, 
0x3f, 0xff, 0x80, 0x00, 0x00, 0x0f, 0xff, 0xf8, 0xff, 0xf8, 0x3f, 0xff, 0x80, 0x00, 0x00, 0x03, 
0xff, 0xf8, 0xff, 0xf8, 0xff, 0xfe, 0x00, 0x00, 0x00, 0x03, 0xff, 0xf8, 0xff, 0xf8, 0xff, 0xfe, 
0x00, 0x00, 0x00, 0x00, 0x1f, 0xf8, 0xff, 0xf8, 0xff, 0xfe, 0x00, 0x00, 0x00, 0x00, 0x1f, 0xf8, 
0xff, 0xf8, 0xff, 0xfe, 0x00, 0x00, 0x00, 0x00, 0x0f, 0xf8, 0xff, 0xe1, 0xff, 0xfc, 0x00, 0x00, 
0x00, 0x00, 0x00, 0x18, 0xff, 0xc7, 0xff, 0xf0, 0x00, 0x00, 0x00, 0x00, 0x00, 0x18, 0xff, 0xc7, 
0xff, 0xf0, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0xff, 0xc7, 0xff, 0xc0, 0x00, 0x00, 0x00, 0x00, 
0x00, 0x00, 0xff, 0xc7, 0xff, 0xc0, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x3f, 0xc7, 0xff, 0x80, 
0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x18, 0x1f, 0xfe, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 
0x18, 0x3f, 0xfe, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x3f, 0xe0, 0x00, 0x00, 0x00, 
0x00, 0x00, 0x00, 0x00, 0x07, 0xff, 0xc0, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x07, 0xff, 
0xc0, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 
0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 
0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 
0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 
0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 
0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00
};

// QR code options

#define qrPixel 4
#define position_x 22
#define position_y 135
#define border 2

// state machine states
enum states {
  none,
  idle,
  interacting,
  dispensing,
  finished
};

states priorstate, state;

String received_message;
float weight, price, total;

void setup() {
  received_message.reserve(2000);
  Serial.begin(9600);
  while (!Serial) {
    ; // wait for serial port to connect. Needed for native USB
  }

  initializeDisplay();
  drawBotoes();
  priorstate = none;
  state = idle;
  tft.setFont(&FreeSans9pt7b);
}


void loop(void){
  switch (state) {
    case idle:
      finished_state();
      break;
    case interacting:
      listening_state();
      break;
    case dispensing:
      dispensing_state();
      break;  
    case finished:
      finished_state();
      break;
  }
}

void idle_state() {
  if(state != priorstate){
    priorstate = state;

    tft.fillScreen(WHITE);
    drawBigLogo();

    tft.setTextColor(BLACK);
    tft.setTextSize(1);
    tft.setCursor(40, 150);
    tft.print("Coffee on Demand");

    tft.fillRoundRect(5, 345, 230, 50, 4, GREEN);

    tft.setTextColor(WHITE);
    tft.setTextSize(1);

    tft.setCursor(95, 375);
    tft.print("Iniciar");

  }

  int button = getTouchButton();
  if(button == 1 || button == 2){
    state = interacting;
  }

  if (state != priorstate) {
    tft.fillScreen(WHITE);
  }
}

void listening_state(){
  if(state != priorstate){
    priorstate = state;
    
    drawListeningBotoes();
    drawListeningText();
  }


  int button = getTouchButton();
  if(button == 1){
    state = interacting;
  }
  if(button == 2){
    state = dispensing;
  }
  if(button == 3){
    state = idle;
  }

  if (state != priorstate) {
    tft.fillScreen(WHITE);
  }
}

void dispensing_state(){

  if(state != priorstate){
    priorstate = state;

    drawLoading();
    drawWeightingBotoes();
  }

  int button = getTouchButton();
  if(button == 1 || button == 2){
    state = finished;
  }

    tft.fillRoundRect(5, 345, 230, 50, 4, GREEN);

    tft.setTextColor(WHITE);
    tft.setTextSize(1);

    tft.setCursor(95, 375);
    tft.print("Continue");

  if (state != priorstate) {
    tft.fillScreen(WHITE);
  }
}

void finished_state(){

  if(state != priorstate){
    priorstate = state;
    sendNumberToPi(20);
    delay(1000);
    received_message = Serial.readStringUntil('\n');
    Serial.println(received_message.c_str());
    drawFinalizado();
    displayQRcode(received_message.c_str());
    received_message = "";
  }

  int button = getTouchButton();
  if(button == 1){
    state = idle;
  }
  if(button == 2){
    state = idle;
  }
  if(button == 3){
    state = idle;
  }

  if (state != priorstate) {
    tft.fillScreen(WHITE);
  }
}

int getTouchButton(){

  int pixel_x, pixel_y;
  TSPoint p = ts.getPoint();
  pinMode(YP, OUTPUT);      //restore shared pins
  pinMode(XM, OUTPUT);
  digitalWrite(YP, HIGH);   //because TFT control pins
  digitalWrite(XM, HIGH);
  bool pressed = (p.z > MINPRESSURE && p.z < MAXPRESSURE);
  if (pressed) {
      pixel_x = map(p.x, TS_LEFT, TS_RT, 0, tft.width()); //.kbv makes sense to me
      pixel_y = map(p.y, TS_TOP, TS_BOT, 0, tft.height());

      // Left button 
      if (pixel_x >= 5 && pixel_x <= 120 && pixel_y >= 345 && pixel_y <= 395) {
        return 1;
      }
      // Right button 
      else if (pixel_x >= 121 && pixel_x <= 235 && pixel_y >= 345 && pixel_y <= 395){
        return 2;
      }
      // Cancel button 
      else if (pixel_x >= 215 && pixel_x <= 235 && pixel_y >= 5 && pixel_y <= 25){
        return 3;
      }
  }

  return -1;
}

void drawBotoes(){
  tft.fillRoundRect(5, 345, 113, 50, 4, COFFEE_ON_DEMAND_2);
  tft.fillRoundRect(122, 345, 113, 50, 4, COFFEE_ON_DEMAND_1);
  tft.fillRoundRect(215, 5, 20, 20, 4, RED);
  
  tft.setTextColor(WHITE);
  tft.setTextSize(1);
  tft.setCursor(219, 20);
  tft.print("X");

  tft.setFont(&FreeSans9pt7b);
  tft.setTextColor(WHITE);
  tft.setTextSize(1);
  tft.setCursor(146, 375);
  tft.print("End");
}

void drawWeightingBotoes(){
  drawBotoes();
  tft.setFont(&FreeSans9pt7b);
  tft.setTextColor(WHITE);
  tft.setTextSize(1);
  tft.setCursor(34, 375);
  tft.print("Interact");
}

void drawListeningBotoes(){
  drawBotoes();
  tft.setFont(&FreeSans9pt7b);
  tft.setTextColor(WHITE);
  tft.setTextSize(1);
  tft.setCursor(34, 375);
  tft.print("Send");
}

void drawText(){
  tft.setTextColor(BLACK);
  tft.setTextSize(3);
  tft.setCursor(18, 120);
  // tft.print(type);
  
  tft.setTextSize(1);
  tft.setCursor(20, 155);
  tft.print("Peso: ");
  tft.print(weight);
  tft.print("kg");
  
  tft.setCursor(20, 178);
  tft.print("Preco/kg: R$");
  tft.print(price);

  tft.fillRect(18,185,204,23,BLACK);

  tft.setTextColor(WHITE);
  tft.setCursor(20, 201);
  tft.print("Custo: R$");
  tft.print(total);

  //240x400
  tft.drawRect(18,138,204,46,BLACK);

  // fruit = "";
  weight = 0;
  price = 0;
  total = 0;
}

void drawListeningText(){
  tft.setTextColor(COFFEE_ON_DEMAND_1);
  tft.setCursor(33, 150);
  tft.setTextSize(2);
  tft.println("Listening...");
  tft.println(""); 
}

void drawBigLogo(){
  tft.drawBitmap(78,155,coffee_bean,75,59,COFFEE_ON_DEMAND_2);//75x59px
}

void drawLoading(){
  tft.setTextColor(COFFEE_ON_DEMAND_1);
  tft.setCursor(33, 150);
  tft.setTextSize(2);
  tft.println("Weighting...");
  tft.setCursor(33, 185);
  tft.setTextSize(1);
  tft.print("Wait while the coffee");
  tft.setCursor(33, 205);
  tft.print(" beans are being");
  tft.setCursor(33, 225);
  tft.print("dispensed.");
  tft.println(""); 
}

void drawFinalizado(){
  tft.setTextColor(COFFEE_ON_DEMAND_1);
  tft.setCursor(25, 47);
  tft.setTextSize(2);
  tft.print("All set!");
  tft.write(0x02);
  tft.println(); 
  tft.setCursor(25, 77);
  tft.setTextSize(1);
  tft.println("To make the payment,");
  tft.setCursor(25, 96);
  tft.println("read the QR-code below "); 
  tft.setCursor(25, 115);
  tft.println("with your banking app"); 
}

void drawFinalizadoBotao(){
  tft.fillRoundRect(5, 345, 230, 50, 4, RED);

  tft.setTextColor(WHITE);
  tft.setTextSize(1);
  tft.setCursor(56, 375);
  tft.print("Continue");
}

void initializeDisplay(){
  uint16_t ID;
  ID = tft.readID();                                                             // valid for Uno shields  

  tft.reset();
  tft.begin (ID);                                                                // initialize SPI bus 
  tft.setRotation (2);                                                           // landscape                                          
  tft.fillScreen (WHITE);
}

#define version 8
uint8_t qrcodeData[301];

void displayQRcode(const char* text){
  QRCode qrcode;
  int size = 4 * version + 17;
  
  qrcode_initText(&qrcode, qrcodeData, version, 0, text);

  tft.fillRoundRect(position_x - border, position_y - border, size*qrPixel + border*2, size*qrPixel + border*2, 4, COFFEE_ON_DEMAND_2);
  tft.fillRoundRect(position_x - border+3, position_y - border+3, size*qrPixel + (border-3)*2, size*qrPixel + (border-3)*2, 4, WHITE);

  for (uint8_t y = 0; y < size; y++) {
    for (uint8_t x = 0; x < size; x++) {
      if(qrcode_getModule(&qrcode,x,y)){
        tft.fillRect(position_x + x*qrPixel, position_y + y*qrPixel, qrPixel, qrPixel, COFFEE_ON_DEMAND_2);
      }
    }
  }
}

void sendNumberToPi(int n){
  Serial.print(n);
  Serial.print("\n");
}

void clearSerialBuffer() {
  while (Serial.available() > 0) {
    Serial.read();
  }
}
