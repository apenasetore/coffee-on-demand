#include <SPI.h>              
#include <Adafruit_GFX.h>                                                      // hardware-specific library
#include <MCUFRIEND_kbv.h>                                                     // hardware-specific library
#include "qrcode.h"
#include <TouchScreen.h>
#include <Fonts/FreeSans9pt7b.h>
//#include <Fonts/FreeSansBold12pt7b.h>

// #include <SdFat.h>                // SD card & FAT filesystem library
// #include <Adafruit_SPIFlash.h>    // SPI / QSPI flash library
// #include <Adafruit_ImageReader.h> // Image-reading functions

// TFT LCD instance
MCUFRIEND_kbv tft;

// SD card usage
// SdFat                SD;         // SD card filesystem
// Adafruit_ImageReader reader(SD); // Image-reader object, pass in SD filesys
// #define SD_CS   10 // SD card select pin
// #define TFT_CS A3 // TFT select pin
// #define TFT_DC  A2 // TFT display/command pin

// Touchscreen definitions
#define MINPRESSURE 200
#define MAXPRESSURE 1000
const int XP=8,XM=A2,YP=A3,YM=9; //240x400 ID=0x7793
// const int TS_LEFT=903,TS_RT=120,TS_TOP=54,TS_BOT=930;
const int TS_LEFT=120,TS_RT=903,TS_TOP=930,TS_BOT=54;
TouchScreen ts = TouchScreen(XP, YP, XM, YM, 300);

// some principal color definitions
// RGB 565 color picker at https://ee-programming-notepad.blogspot.com/2016/10/16-bit-color-generator-picker.html
#define WHITE       0xFFFF
#define BLACK       0x0000
#define RED         0xF800
#define GREEN       0x0f0f
#define WE_SCALE_1  0x5bd9
#define WE_SCALE_2  0x212a

// 'Logo', 36x29px
//const unsigned char logo [] PROGMEM = {
//  0x4a, 0x00, 0xc0, 0x02, 0x00, 0x4a, 0x01, 0xa0, 0x02, 0x00, 0x4a, 0x71, 0x26, 0x32, 0xe0, 0x4a, 
//  0x90, 0x8b, 0x0a, 0xa0, 0x4a, 0xd0, 0x48, 0x0a, 0xa0, 0x4a, 0xe0, 0x28, 0x3a, 0xe0, 0x4a, 0x81, 
//  0x28, 0x4a, 0x80, 0x4a, 0x91, 0x2b, 0x4a, 0xa0, 0x7e, 0x71, 0xc6, 0x32, 0xe0, 0x00, 0x00, 0x00, 
//  0x00, 0x00, 0xff, 0xff, 0xff, 0xff, 0xf0, 0x7f, 0xff, 0xff, 0xff, 0xe0, 0x7f, 0xff, 0xff, 0xff, 
//  0xe0, 0x3f, 0xff, 0xff, 0xff, 0xc0, 0x00, 0x02, 0x04, 0x00, 0x00, 0x00, 0x1e, 0x07, 0x80, 0x00, 
//  0x00, 0xe0, 0x00, 0x70, 0x00, 0x00, 0x80, 0x60, 0x10, 0x00, 0x00, 0x81, 0x98, 0x10, 0x00, 0x01, 
//  0x82, 0x44, 0x18, 0x00, 0x01, 0x02, 0x44, 0x08, 0x00, 0x01, 0x02, 0x64, 0x08, 0x00, 0x03, 0x02, 
//  0x04, 0x0c, 0x00, 0x02, 0x01, 0x98, 0x04, 0x00, 0x02, 0x00, 0x60, 0x04, 0x00, 0x03, 0x00, 0x00, 
//  0x0c, 0x00, 0x03, 0xff, 0xff, 0xfc, 0x00, 0x00, 0xc0, 0x00, 0x30, 0x00, 0x00, 0xc0, 0x00, 0x30, 
//  0x00
//};

//// 'big_logo', 75x59px
const unsigned char big_logo [] PROGMEM = {
  0x00, 0x00, 0x00, 0x00, 0x38, 0x00, 0x00, 0x06, 0x00, 0x00, 0x31, 0x86, 0x00, 0x00, 0xe6, 0x00, 
  0x00, 0x06, 0x00, 0x00, 0x31, 0x86, 0x00, 0x00, 0xc2, 0x00, 0x00, 0x06, 0x00, 0x00, 0x31, 0x86, 
  0x00, 0x00, 0xc2, 0x00, 0x00, 0x06, 0x00, 0x00, 0x31, 0x86, 0x06, 0x00, 0xc2, 0x06, 0x03, 0x06, 
  0x06, 0x00, 0x31, 0x86, 0x19, 0x80, 0xc0, 0x19, 0x0c, 0xc6, 0x19, 0x80, 0x31, 0x86, 0x31, 0x80, 
  0xe0, 0x39, 0x8c, 0xc6, 0x18, 0xc0, 0x31, 0x86, 0x31, 0x80, 0x70, 0x31, 0x8c, 0x66, 0x18, 0xc0, 
  0x31, 0x86, 0x31, 0x80, 0x38, 0x30, 0x0c, 0x66, 0x18, 0xc0, 0x31, 0x86, 0x31, 0x80, 0x0c, 0x30, 
  0x03, 0x66, 0x18, 0xc0, 0x31, 0x86, 0x31, 0x80, 0x0e, 0x30, 0x0f, 0xe6, 0x18, 0xc0, 0x31, 0x86, 
  0x31, 0x80, 0x06, 0x30, 0x0c, 0xe6, 0x18, 0xc0, 0x31, 0x86, 0x3f, 0x80, 0xc2, 0x30, 0x0c, 0x66, 
  0x1f, 0x80, 0x31, 0x86, 0x30, 0x00, 0xc2, 0x30, 0x0c, 0x66, 0x18, 0x00, 0x31, 0x86, 0x31, 0x80, 
  0xc2, 0x30, 0x0c, 0x66, 0x18, 0xc0, 0x31, 0x86, 0x31, 0x80, 0xc2, 0x30, 0x0c, 0x66, 0x18, 0xc0, 
  0x31, 0x86, 0x31, 0x80, 0xc2, 0x31, 0x8c, 0x66, 0x18, 0xc0, 0x31, 0xce, 0x19, 0x80, 0xc6, 0x39, 
  0x8c, 0xe6, 0x18, 0xc0, 0x1f, 0xfc, 0x1f, 0x80, 0x7c, 0x1f, 0x0f, 0xc6, 0x0f, 0x80, 0x04, 0x30, 
  0x06, 0x00, 0x38, 0x06, 0x03, 0x00, 0x07, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 
  0x00, 0x00, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xe0, 0xff, 0xff, 0xff, 0xff, 
  0xff, 0xff, 0xff, 0xff, 0xff, 0xe0, 0x7f, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xc0, 
  0x20, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x80, 0x30, 0x00, 0x00, 0x00, 0x00, 0x00, 
  0x00, 0x00, 0x01, 0x80, 0x18, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x03, 0x00, 0x1c, 0x00, 
  0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x0e, 0x00, 0x0f, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 
  0xfc, 0x00, 0x00, 0x00, 0x00, 0x03, 0x00, 0x18, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x03, 
  0x00, 0x18, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x03, 0x00, 0x18, 0x00, 0x00, 0x00, 0x00, 
  0x00, 0x00, 0x00, 0x03, 0x00, 0x18, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x07, 0xff, 0xff, 0xff, 
  0xfc, 0x00, 0x00, 0x00, 0x00, 0x00, 0x1c, 0x00, 0x00, 0x00, 0x0f, 0x00, 0x00, 0x00, 0x00, 0x00, 
  0x38, 0x00, 0x0e, 0x00, 0x03, 0x00, 0x00, 0x00, 0x00, 0x00, 0x60, 0x00, 0x31, 0x80, 0x01, 0x80, 
  0x00, 0x00, 0x00, 0x00, 0x60, 0x00, 0xe0, 0xe0, 0x00, 0x80, 0x00, 0x00, 0x00, 0x00, 0x40, 0x01, 
  0x00, 0x10, 0x00, 0xc0, 0x00, 0x00, 0x00, 0x00, 0xc0, 0x01, 0x04, 0x10, 0x00, 0xc0, 0x00, 0x00, 
  0x00, 0x00, 0x80, 0x03, 0x04, 0x18, 0x00, 0x40, 0x00, 0x00, 0x00, 0x00, 0x80, 0x02, 0x0e, 0x08, 
  0x00, 0x40, 0x00, 0x00, 0x00, 0x00, 0x80, 0x04, 0x15, 0x04, 0x00, 0x40, 0x00, 0x00, 0x00, 0x00, 
  0x80, 0x04, 0x24, 0x84, 0x00, 0x20, 0x00, 0x00, 0x00, 0x01, 0x80, 0x04, 0x11, 0x04, 0x00, 0x20, 
  0x00, 0x00, 0x00, 0x01, 0x00, 0x02, 0x0a, 0x08, 0x00, 0x20, 0x00, 0x00, 0x00, 0x01, 0x00, 0x03, 
  0x04, 0x18, 0x00, 0x20, 0x00, 0x00, 0x00, 0x01, 0x00, 0x01, 0x00, 0x10, 0x00, 0x20, 0x00, 0x00, 
  0x00, 0x03, 0x00, 0x01, 0x00, 0x10, 0x00, 0x30, 0x00, 0x00, 0x00, 0x03, 0x00, 0x00, 0xe0, 0xe0, 
  0x00, 0x10, 0x00, 0x00, 0x00, 0x03, 0x00, 0x00, 0x31, 0x80, 0x00, 0x10, 0x00, 0x00, 0x00, 0x03, 
  0x00, 0x00, 0x0e, 0x00, 0x00, 0x18, 0x00, 0x00, 0x00, 0x02, 0x00, 0x00, 0x00, 0x00, 0x00, 0x18, 
  0x00, 0x00, 0x00, 0x03, 0xff, 0xff, 0xff, 0xff, 0xff, 0xf8, 0x00, 0x00, 0x00, 0x00, 0x60, 0x00, 
  0x00, 0x00, 0x00, 0xc0, 0x00, 0x00, 0x00, 0x00, 0x60, 0x00, 0x00, 0x00, 0x00, 0xc0, 0x00, 0x00, 
  0x00, 0x00, 0x60, 0x00, 0x00, 0x00, 0x00, 0xc0, 0x00, 0x00, 0x00, 0x00, 0x60, 0x00, 0x00, 0x00, 
  0x00, 0xc0, 0x00, 0x00, 0x00, 0x00, 0x7f, 0xff, 0xff, 0xff, 0xff, 0xc0, 0x00, 0x00
};

// QR code options

#define qrPixel 4
#define position_x 22
#define position_y 135
#define border 5

// state machine states
enum states {
  none,
  inicio,
  pesando,
  pesado,
  finalizado
};

states priorstate, state;

// String for serial read
String received_message="";


String fruit, weightStr, totalStr, priceStr;
float weight, price, total;

void setup() {
  Serial.begin(9600);
  while (!Serial) {
    ; // wait for serial port to connect. Needed for native USB
  }
  received_message.reserve(1000);
  initializeDisplay();
  //drawLogo();
  drawBotoes();
  priorstate = none;
  state = inicio;
  tft.setFont(&FreeSans9pt7b);
}


void loop(void){
  switch (state) {
    case inicio:
      inicio_state();
      break;
    case pesando:
      pesando_state();
      break;
    case pesado:
      pesado_state();
      break;
    case finalizado:
      finalizado_state();
      break;
  }
}

// /*
void inicio_state() {
  // Tarefas de entrada do estado
  if(state != priorstate){
    priorstate = state;

    //coisas da inicializaï¿½ï¿½o do estado inicial: ...
    tft.fillScreen(WHITE);
    drawBigLogo();

    // Buttons
    tft.fillRoundRect(5, 345, 230, 50, 4, GREEN);

    tft.setTextColor(WHITE);
    tft.setTextSize(1);

    tft.setCursor(95, 375);
    tft.print("Iniciar");

  }

  //tarefas do estado inicial: ...

  // Check for state transitions
  int button = getTouchButton();
  if(button == 1 || button == 2){
    state = pesando;
  }

  // Tarefas de saï¿½da do estado
  if (state != priorstate) {
    tft.fillScreen(WHITE);
  }
}

void pesando_state(){
  // Tarefas de entrada do estado
  if(state != priorstate){
    sendNumberToPi(10);
    priorstate = state;

    //coisas da inicializaï¿½ï¿½o do estado pesando: ...
    // Serial.write()
    //drawLogo();
    drawLoading();
    //drawBotoes();
  }

  //tarefas do estado pesando: ...
  

  // Check for state transitions
  while(!Serial.available()){
    ;
  }
  received_message = Serial.readStringUntil('\n');  //read until timeout
  received_message.trim();
  
  if(received_message){
//    Serial.print("Recebi: ");
//    Serial.println(received_message);
    parseInput(received_message);
    state = pesado;
  }
  
  // if("cancelar"){
  //   state = inicio;
  // }

  // Tarefas de saï¿½da do estado
  if (state != priorstate) {
    tft.fillScreen(WHITE);
  }
}

void pesado_state(){
  // Tarefas de entrada do estado
  if(state != priorstate){
    priorstate = state;
    
    //coisas da inicializaï¿½ï¿½o do estado pesado: ...
    //drawLogo();
    drawBotoes();
    drawText();
  }

  //tarefas do estado pesado: ...

  // Check for state transitions

  int button = getTouchButton();
  if(button == 1){
    state = pesando;
  }
  if(button == 2){
    state = finalizado;
  }
  if(button == 3){
    state = inicio;
  }

  // Tarefas de saï¿½da do estado
  if (state != priorstate) {
    tft.fillScreen(WHITE);
  }
}

void finalizado_state(){
  // Tarefas de entrada do estado
  if(state != priorstate){
    priorstate = state;
    clearSerialBuffer();
    sendNumberToPi(20);
    while(!Serial.available()){
    ;
    }
    received_message = Serial.readStringUntil('\n');  //read until timeout
    received_message.trim();
    //coisas da inicializaï¿½ï¿½o do estado finalizado: ...
    drawFinalizado();
    displayQRcode(received_message.c_str());
    received_message = "";
    drawFinalizadoBotao();
  }

  //tarefas do estado finalizado: ...

  // Check for state transitions
  int button = getTouchButton();
  if(button == 1){
    state = inicio;
  }
  if(button == 2){
    state = inicio;
  }
  if(button == 3){
    state = inicio;
  }

  // Tarefas de saï¿½da do estado
  if (state != priorstate) {
    tft.fillScreen(WHITE);
  }
}
//*/

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
  tft.fillRoundRect(5, 345, 113, 50, 4, WE_SCALE_2);
  tft.fillRoundRect(122, 345, 113, 50, 4, WE_SCALE_1);
  tft.fillRoundRect(215, 5, 20, 20, 4, RED);
  
  tft.setTextColor(WHITE);
  tft.setTextSize(1);
  tft.setCursor(219, 20);
  tft.print("X");

  tft.setFont(NULL);
  tft.setTextColor(WHITE);
  tft.setTextSize(3);
  tft.setCursor(54, 358);
  tft.print("+");

  tft.setFont(&FreeSans9pt7b);
  tft.setTextColor(WHITE);
  tft.setTextSize(1);
  tft.setCursor(146, 375);
  tft.print("Finalizar");

}

void drawText(){
  tft.setTextColor(BLACK);
  tft.setTextSize(3);
  tft.setCursor(18, 120);
  tft.print(fruit);
  
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

  fruit = "";
  weight = 0;
  price = 0;
  total = 0;
}

void drawBigLogo(){
  tft.drawBitmap(78,155,big_logo,75,59,WE_SCALE_2);//75x59px
}

void drawLoading(){
  tft.setTextColor(WE_SCALE_1);
  tft.setCursor(33, 150);
  tft.setTextSize(2);
  tft.println("Pesando...");
  tft.setCursor(33, 185);
  tft.setTextSize(1);
  tft.print("Coloque a fruta no");
  tft.setCursor(33, 205);
  tft.print("centro do prato da");
  tft.setCursor(33, 225);
  tft.print("balanca.");
  tft.println(""); 
}

void drawFinalizado(){
  tft.setTextColor(WE_SCALE_1);
  tft.setCursor(25, 47);
  tft.setTextSize(2);
  tft.print("Pronto!");
  tft.write(0x02);
  tft.println(); 
  tft.setCursor(25, 77);
  tft.setTextSize(1);
  tft.println("Para efetuar o pagamento,");
  tft.setCursor(25, 96);
  tft.println("leia o QR-code abaixo "); 
  tft.setCursor(25, 115);
  tft.println("no app WeScale!"); 
}

void drawFinalizadoBotao(){
  tft.fillRoundRect(5, 345, 230, 50, 4, RED);

  tft.setTextColor(WHITE);
  tft.setTextSize(1);
  tft.setCursor(56, 375);
  tft.print("Nova compra");
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

  tft.fillRoundRect(position_x - border, position_y - border, size*qrPixel + border*2, size*qrPixel + border*2, 4, WE_SCALE_2);
  tft.fillRoundRect(position_x - border+3, position_y - border+3, size*qrPixel + (border-3)*2, size*qrPixel + (border-3)*2, 4, WHITE);

  for (uint8_t y = 0; y < size; y++) {
    for (uint8_t x = 0; x < size; x++) {
      if(qrcode_getModule(&qrcode,x,y)){
        tft.fillRect(position_x + x*qrPixel, position_y + y*qrPixel, qrPixel, qrPixel, WE_SCALE_2);
      }
    }
  }
}

// Function to parse the input string

void parseInput(String input) {
  int firstUnderscoreIndex = input.indexOf('_');
  int secondUnderscoreIndex = input.indexOf('_', firstUnderscoreIndex + 1);
  int thirdUnderscoreIndex = input.indexOf('_', secondUnderscoreIndex + 1);
  
  fruit = input.substring(0, firstUnderscoreIndex);
  weightStr = input.substring(firstUnderscoreIndex + 1, secondUnderscoreIndex);
  totalStr = input.substring(secondUnderscoreIndex + 1, thirdUnderscoreIndex);
  priceStr = input.substring(thirdUnderscoreIndex + 1);
  
  weight = weightStr.toFloat();
  total = totalStr.toFloat();
  price = priceStr.toFloat();
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
