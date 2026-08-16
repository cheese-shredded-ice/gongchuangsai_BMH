#ifndef __CAR_H
#define __CAR_H
#include "stm32f4xx.h"
#include "usart.h"
#include "delay.h"
#include "board.h"
#include "Emm_V5.h"
#include "uart6_ckp.h"
#include "Serial.h"
#include "yyb_move.h"
#include "imu.h"
#include "PWM.h"
#include "LED.h"
#include "OLED.h"
#include "swith.h"
#include "pid.h"
#include "usart5.h"
#include "wit_c_sdk.h"
#include "exti.h"

//x减物块右移（从外侧往内看）//y+物块往地图内侧走
//x加物块左移（从外侧往内看）//y-物块往地图外侧走
#define  x_center_red       955
#define  y_center_red		519

#define  x_center_green		955
#define  y_center_green		519

#define  x_center_blue		955
#define  y_center_blue		519


void transfer_pi_position11();
void transfer_pi_position12();
void transfer_pi_position2();
void transfer_pi_position3();
void fangzhi_green();
void fangzhi_red();
void fangzhi_blue();
void fangzhi();
void fangzhi_maduo();
void na();
void yuantai_na();
void yuantai_na1();
void yuantai_na2();
void yuantai_fang();
void yuantai_fang1();
void yuantai_fang2();

void wait_send_shumeipai();
void clear_ckp();
void jixie_reset();
void car_Init();
void map();

extern char tjcstr[100];
extern int acc[4];
extern float direct_x;
extern float direct_y;
extern float distance_wukuai;
extern float x_origin;
extern float y_origin;
extern float time_zhua;
extern int task[6]; //存储颜色信息
extern int ypcode[6]; //存储颜色信息
extern int move[6]; //存储移动信息
extern int test11;
extern float angle;


#endif
