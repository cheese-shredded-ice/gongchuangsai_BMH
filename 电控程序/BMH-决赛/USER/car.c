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

//搭配set_XXX()使用，直接改这里的数值
float zhuanpan1[3]={-71.0f , 20.0f , 247.0f};//转盘一号位
float zhuanpan2[3]={90.0f  , 20.0f , 267.0f};//转盘二号位
float zhuanpan3[3]={92.0f  , 20.0f , 220.0f};//转盘三号位

float fangzhi1[3]={56.0f , 125.0f , 198.4f};//红 放和拿
float fangzhi2[3]={3.0f  , 125.0f , 249.5f};//绿 放和拿
float fangzhi3[3]={59.8f , 125.0f , 298.5f};//蓝 放和拿

float maduo1[3]={60.5f , 55.0f , 195.5f};//红 码垛
float maduo2[3]={1.8f  , 55.0f , 246.0f};//绿 码垛
float maduo3[3]={50.0f , 53.0f , 298.6f};//蓝 码垛

char tjcstr[100];
int acc[4];
float direct_x = 0;
float direct_y = 0;
float distance_wukuai = 150;
float x_origin = 0;
float y_origin = 0;
float time_zhua = 0;
int task[6]; //存储颜色信息
int ypcode[6]; //存储颜色信息
int move[6]; //存储移动信息
int test11 = 0;
float angle = 0;



void transfer_pi_position11(uint8_t task_num);
void transfer_pi_position12(uint8_t task_num);
void transfer_pi_position2(void);
void transfer_pi_position3(uint8_t task_num);
void transfer_pi_position4(uint8_t task_num);
void yuantai_fang0(void);
void fangzhi_green(void);
void fangzhi_red(void);
void fangzhi_blue(void);
void fangzhi(uint8_t task);
void fangzhi_maduo(uint8_t task);
void na(uint8_t task);
void yuantai_na(uint8_t task);
void yuantai_na1(uint8_t task);
void yuantai_na2(uint8_t task);
void yuantai_fang0(void);
void yuantai_fang(uint8_t task);
void yuantai_fang1(uint8_t task);
void yuantai_fang2(uint8_t task);
void wait_send_shumeipai(uint8_t message,uint16_t time);
void clear_ckp(void);
void jixie_reset(void);
void m(int a, int b);
void map(uint8_t a, uint8_t b);

// 路径规划函数，根据起点 a 和终点 b 执行对应的移动序列
// a, b 含义：
// 0-起点  1-正上方  2-物料盘  3-正左  4-正右  5-正下
void m(int a, int b)
{
	
	if(a == 0&&b== 1){
	
	car_move2(150,0,150,150);
	car_move1(0,-1035,150,200);

	}
	
	if(a == 1&&b== 5){
	
	mypid.integral = 0;PID_move(0,0,0,1000,90,0);//在原地旋转
	PID_move(0,0,0,1000,90,3);
	
	car_move1(0,-1700,200,250);//快速通过
	
	mypid.integral = 0;PID_move(0,0,0,1000,-180,0);//在粗加工区原地旋转
	PID_move(0,0,0,1000,-180,3);
	}



	
	if(a == 0&&b== 3){
		
	car_move2(180,0,150,150);
	car_move1(0,-1860,150,200);
		
	mypid.integral = 0;PID_move(0,0,0,1000,90,0);//在原地旋转
	PID_move(0,0,0,1000,90,3);
	
	car_move1(0,-900,200,200);//快速通过
	}
	
	if(a == 3&&b== 4){
		
	mypid.integral = 0;PID_move(0,0,0,1000,0,0);//在原地旋转
	PID_move(0,0,0,1000,0,3);
	
	car_move1(0,1700,200,200);//快速通过
	
	mypid.integral = 0;PID_move(0,0,0,1000,-90,0);//在粗加工区原地旋转
	PID_move(0,0,0,1000,-90,3);
	
	
	}
	
	if(a == 4&&b== 5){
	car_move1(0,800,150,200);
		
	mypid.integral = 0;PID_move(0,0,0,1000,-180,0);//在原地旋转
	PID_move(0,0,0,1000,-180,3);
	
	car_move1(0,900,150,200);
	}

	if(a == 5&&b== 0){
	
	car_move2(60,0,150,150);
	car_move1(0,-1000,150,150);
	

	car_move2(-160,0,150,150);

	
	}
}

void map(uint8_t a, uint8_t b)
{
	if(a==0){
		if(b==1)
		{ m(0,1); }
		if(b==3)
		{ m(0,3); }
		if(b==5) 
		{ m(0,1); m(1,5);}
		
	}else if(a==3){
		if(b==4)
		{ m(3,4); }
	}else if(a==4){
		if(b==5)
		{ m(4,5); }
	}else if(a==5){
		if(b==0)
		{ m(5,0);}
	}else if(a==1){
		if(b==5)
		{ m(1,5); }
	}
}




void fangzhi(uint8_t task)
{
	if(task == 0x01){
		fangzhi_red();
	}else if(task == 0x02){
		fangzhi_green();
	}else if(task == 0x03){
		fangzhi_blue();
	}
}

void fangzhi_red(void)
{
	move_all(0.0f,1000,200    ,0,1000,245   ,70,13);
	move_all(10.0f,1000,200   ,0,1000,245   ,fangzhi1[2],13);
	delay_ms1(200);
	move_all(fangzhi1[0],1000,200   ,0,1000,245   ,fangzhi1[2],13);//拆分并加延时
	delay_ms1(300);
	move_all(fangzhi1[0],1000,200   ,fangzhi1[1],1000,245   ,fangzhi1[2],13);
	
	set_zhuashou_Angle_kai();
	
}

void fangzhi_green(void)
{
	move_all(0.0f,1000,200    ,0,1000,245   ,70,13);
	move_all(10.0f,1000,200   ,0,1000,245   ,fangzhi2[2],13);
	delay_ms1(200);
	move_all(fangzhi2[0],1000,200   ,0,1000,245   ,fangzhi2[2],13);//拆分并加延时
	delay_ms1(300);
	move_all(fangzhi2[0],1000,200   ,fangzhi2[1],1000,245   ,fangzhi2[2],13);
	set_zhuashou_Angle_kai();
}


void fangzhi_blue(void)
{
	move_all(0.0f,1000,200    ,0,1000,245   ,70,13);
	move_all(10.0f,1000,200   ,0,1000,245   ,fangzhi3[2],13);
	delay_ms1(200);
	move_all(fangzhi3[0],1000,200   ,0,1000,245   ,fangzhi3[2],13);//拆分并加延时
	delay_ms1(300);
	move_all(fangzhi3[0],1000,200   ,fangzhi3[1],1000,245   ,fangzhi3[2],13);
	
	set_zhuashou_Angle_kai();
}



void na_red(void)
{	
	move_all(fangzhi1[0],1000,200   ,fangzhi1[1],1000,200   ,fangzhi1[2],13);
	set_zhuashou_Angle_he();
	move_all(fangzhi1[0],1000,200   ,20,1000,200   ,fangzhi1[2],13);
	move_all(10.0f,1000,200   ,0,1000,200   ,70,13);
	move_all(0.0f,1000,200   ,20,1000,200   ,70,13);
	set_zhuashou_Angle_kai();
}

void na_green(void)
{
	move_all(fangzhi2[0],1000,200   ,fangzhi2[1],1000,200   ,fangzhi2[2],13);
	set_zhuashou_Angle_he();
	move_all(fangzhi2[0],1000,200   ,20,1000,200   ,fangzhi2[2],13);
	move_all(10.0f,1000,200   ,0,1000,200   ,70,13);
	move_all(0.0f,1000,200   ,20,1000,200   ,70,13);
	set_zhuashou_Angle_kai();
	
}

void na_blue(void)
{
	move_all(fangzhi3[0],1000,200   ,100,1000,200   ,fangzhi3[2],13);
	move_all(fangzhi3[0],1000,200   ,fangzhi3[1],1000,200   ,fangzhi3[2],13);
	set_zhuashou_Angle_he();
	move_all(fangzhi3[0],1000,200   ,20,1000,200   ,fangzhi3[2],13);
	move_all(10.0f,1000,200   ,0,1000,200   ,70,13);
	move_all(0.0f,1000,200   ,20,1000,200   ,70,13);
	set_zhuashou_Angle_kai();
	
}


void na(uint8_t task)
{
	if(task == 0x01){
		na_red();
	}else if(task == 0x02){
		na_green();
	}else if(task == 0x03){
		na_blue();
	}
}


void fangzhi_maduo(uint8_t task)
{
	if(task == 0x01){
		delay_ms1((int)shengjiang_control(0,1000,200));
		
		move_all(maduo1[0],1000,200   ,0,1000,200   ,maduo1[2],11);
		
		move_all(maduo1[0],1000,200   ,maduo1[1],1000,200   ,maduo1[2],11);
		delay_ms1(500);

		set_zhuashou_Angle(45.0f,300);
	}else if(task == 0x02){
		delay_ms1((int)shengjiang_control(0,1000,200));
		
//		move_all(3.0f,1000,200   ,0,1000,200   ,152,11);
		
		move_all(maduo2[0],1000,200   ,0,1000,200   ,maduo2[2],11);
		
		move_all(maduo2[0],1000,200   ,maduo2[1],1000,200   ,maduo2[2],11);
		delay_ms1(500);

		set_zhuashou_Angle(45.0f,300);
	}else if(task == 0x03){
		delay_ms1((int)shengjiang_control(0,1000,200));
		
		move_all(10.0f,1000,200   ,0,1000,200   ,152,11);
		
		move_all(maduo3[0]-120,1000,200   ,0,1000,200   ,maduo3[2],11);;
		delay_ms1(100);
		move_all(maduo3[0],1000,200   ,maduo3[1],1000,200   ,maduo3[2],11);
		delay_ms1(500);

		set_zhuashou_Angle(45.0f,300);
	}
}


void yuantai_na(uint8_t task)
{
	if(task == 0x01){
		time_zhua += move_all(zhuanpan1[0],1000,200   ,zhuanpan1[1],1000,200   ,zhuanpan1[2],11);
		delay_ms1(1000);
		set_zhuashou_Angle_he();    time_zhua += 350;
		
		time_zhua += move_all(10.0f,1000,200   ,0,1000,200   ,70,11);
		delay_ms1(100);
		time_zhua += move_all(0.0f,1000,200   ,30,1000,200   ,70,11);//30,1000,200,无延时
		delay_ms1(100);
		set_zhuashou_Angle(45.0f,300);	 time_zhua += 350;

	}else if(task == 0x02){
		time_zhua += move_all(zhuanpan2[0],1000,200   ,zhuanpan2[1],1000,200   ,zhuanpan2[2],11);
		delay_ms1(1000);
		
		set_zhuashou_Angle_he();   time_zhua += 350;
		
		time_zhua += move_all(10.0f,1000,200   ,0,1000,200   ,70,11);
		delay_ms1(100);
		time_zhua += move_all(0.0f,1000,200   ,30,1000,200   ,70,11);//
		delay_ms1(100);
		set_zhuashou_Angle(45.0f,300);   time_zhua += 350;

	}else if(task == 0x03){
		time_zhua += move_all(zhuanpan3[0],1000,200   ,zhuanpan3[1],1000,200   ,zhuanpan3[2],11);
		delay_ms1(1000);
		set_zhuashou_Angle_he();   time_zhua += 350;
		
		time_zhua += move_all(10.0f,1000,200   ,0,1000,200   ,70,11);
		delay_ms1(100);
		time_zhua += move_all(0.0f,1000,200   ,30,1000,200   ,70,11);//
		delay_ms1(100);
		set_zhuashou_Angle(45.0f,300);   time_zhua += 350;
	}
}

void yuantai_na1(uint8_t task)
{
	if(task == 0x01){
		set_zhuashou_Angle(40.0f,300);   time_zhua += 350;
		time_zhua += move_all(zhuanpan1[0],1000,200   ,zhuanpan1[1],1000,200   ,zhuanpan1[2],11);
		
	}else if(task == 0x02){
		set_zhuashou_Angle(40.0f,300);	 time_zhua += 350;
		time_zhua += move_all(0,1000,200   ,zhuanpan2[1],1000,200   ,zhuanpan2[2],11);
	}else if(task == 0x03){
		set_zhuashou_Angle(40.0f,300);   time_zhua += 350;
		time_zhua += move_all(0,1000,200   ,zhuanpan3[1],1000,200   ,zhuanpan3[2],11);
	}
}

void yuantai_na2(uint8_t task)
{
	if(task == 0x01){
		time_zhua += move_all(zhuanpan1[0],1000,200   ,zhuanpan1[1],1000,200   ,zhuanpan1[2],11);
		delay_ms1(1000);
		set_zhuashou_Angle(0.1f,300);    time_zhua += 350;
		time_zhua += move_all(0.0f,1000,200   ,0,1000,200   ,70,11);
		time_zhua += move_all(0.0f,1000,200   ,30,1000,200   ,70,11);
		set_zhuashou_Angle(45.0f,300);	 time_zhua += 350;

	}else if(task == 0x02){
		time_zhua += move_all(zhuanpan2[0],1000,200   ,zhuanpan2[1],1000,200   ,zhuanpan2[2],11);
		delay_ms1(1000);
		set_zhuashou_Angle(0.5f,300);    time_zhua += 350;
		
		time_zhua += move_all(0.0f,1000,200   ,0,1000,200   ,70,11);
		time_zhua += move_all(0.0f,1000,200   ,30,1000,200   ,70,11);
		set_zhuashou_Angle(45.0f,300);   time_zhua += 350;

	}else if(task == 0x03){
		time_zhua += move_all(zhuanpan3[0],1000,200   ,zhuanpan3[1],1000,200   ,zhuanpan3[2],11);
		delay_ms1(1000);
		set_zhuashou_Angle(0.5f,300);    time_zhua += 350;
		time_zhua += move_all(10.0f,1000,200   ,0,1000,200   ,70,11);
		time_zhua += move_all(0.0f,1000,200   ,30,1000,200   ,70,11);
		set_zhuashou_Angle(45.0f,300);   time_zhua += 350;
	}
}

void yuantai_fang0(void)
{
	set_zhuashou_Angle_kai();
	move_all(0.0f,1000,200   ,20,1000,200   ,70,13);//复位
	move_all(0.0f,1000,200   ,35,1000,200   ,70,13);//物块平台抓物块
	set_zhuashou_Angle_he();
	delay_ms1((int)shengjiang_control(0,1000,200));
//	time_zhua += move_all(10.0f,1000,200   ,0,1000,200   ,247,11);
	time_zhua += move_all(80.0f,1000,200   ,0,1000,200   ,247,11);
}


void yuantai_fang(uint8_t task)
{
	if(task == 0x01){
//		time_zhua += move_all(0.0f,1000,200   ,0,1000,200   ,70,11);
//		time_zhua += move_all(0.0f,1000,200   ,35,1000,200   ,70,11);
//		set_zhuashou_Angle_he();
//		delay_ms1((int)shengjiang_control(0,1000,200));
		
		time_zhua += move_all(0,1000,200   ,0,1000,200   ,zhuanpan1[2],11);
		time_zhua += move_all(zhuanpan1[0],1000,200   ,0,1000,200   ,zhuanpan1[2],11);
		time_zhua += move_all(zhuanpan1[0],1000,200   ,zhuanpan1[1],1000,200   ,zhuanpan1[2],11);
		set_zhuashou_Angle(40.0f,300);    time_zhua += 350;
		delay_ms1((int)shengjiang_control(0,1000,200));
		

	}else if(task == 0x02){
//		time_zhua += move_all(0.0f,1000,200   ,0,1000,200   ,70,11);
//		time_zhua += move_all(0.0f,1000,200   ,35,1000,200   ,70,11);
//		set_zhuashou_Angle_he();
//		delay_ms1((int)shengjiang_control(0,1000,200));
		
//		time_zhua += move_all(40,1000,200   ,0,1000,200   ,zhuanpan2[2],11);
		time_zhua += move_all(zhuanpan2[0],1000,200   ,0,1000,200   ,zhuanpan2[2],11);
		time_zhua += move_all(zhuanpan2[0],1000,200   ,zhuanpan2[1],1000,200   ,zhuanpan2[2],11);
		set_zhuashou_Angle(40.0f,300);  time_zhua += 350;
		delay_ms1((int)shengjiang_control(0,1000,200));
		

	}else if(task == 0x03){
//		time_zhua += move_all(0.0f,1000,200   ,0,1000,200   ,70,11);
//		time_zhua += move_all(0.0f,1000,200   ,35,1000,200   ,70,11);
//		set_zhuashou_Angle_he();
//		delay_ms1((int)shengjiang_control(0,1000,200));
		
//		time_zhua += move_all(40,1000,200   ,0,1000,200   ,zhuanpan3[2],11);
		time_zhua += move_all(zhuanpan3[0],1000,200   ,0,1000,200   ,zhuanpan3[2],11);
		time_zhua += move_all(zhuanpan3[0],1000,200   ,zhuanpan3[1],1000,200   ,zhuanpan3[2],11);
		set_zhuashou_Angle(40.0f,300);   time_zhua += 350;
		delay_ms1((int)shengjiang_control(0,1000,200));
		
	}
}

void yuantai_fang1(uint8_t task)
{
	if(task == 0x01){
		

		delay_ms1((int)shengjiang_control(0,1000,200));
		
		time_zhua += move_all(zhuanpan1[0],1000,200   ,0,1000,200   ,zhuanpan1[2],11);
		
	}else if(task == 0x02){
		delay_ms1((int)shengjiang_control(0,1000,200));
		
		time_zhua += move_all(-20,1000,200   ,0,1000,200   ,zhuanpan2[2],11);
		
	}else if(task == 0x03){
		delay_ms1((int)shengjiang_control(0,1000,200));
		
		time_zhua += move_all(-20,1000,200   ,0,1000,200   ,zhuanpan3[2],11);
	}
}

void yuantai_fang2(uint8_t task)
{
	if(task == 0x01){
		time_zhua += move_all(0.0f,1000,200   ,0,1000,200   ,70,11);
		time_zhua += move_all(0.0f,1000,200   ,35,1000,200   ,70,11);
		set_zhuashou_Angle_he();
		delay_ms1((int)shengjiang_control(0,1000,200));
		
		time_zhua += move_all(40,1000,200   ,0,1000,200   ,zhuanpan1[2],11);
		time_zhua += move_all(zhuanpan1[0],1000,200   ,0,1000,200   ,zhuanpan1[2],11);
		time_zhua += move_all(zhuanpan1[0],1000,200   ,zhuanpan1[1],1000,200   ,zhuanpan1[2],11);
		set_zhuashou_Angle(40.0f,300);    time_zhua += 350;
		delay_ms1((int)shengjiang_control(0,1000,200));
		

	}else if(task == 0x02){
		time_zhua += move_all(0.0f,1000,200   ,0,1000,200   ,70,11);
		time_zhua += move_all(0.0f,1000,200   ,35,1000,200   ,70,11);
		set_zhuashou_Angle_he();
		delay_ms1((int)shengjiang_control(0,1000,200));
		
		time_zhua += move_all(40,1000,200   ,0,1000,200   ,zhuanpan2[2],11);
		time_zhua += move_all(zhuanpan2[0],1000,200   ,0,1000,200   ,zhuanpan2[2],11);
		time_zhua += move_all(zhuanpan2[0],1000,200   ,zhuanpan2[1],1000,200   ,zhuanpan2[2],11);
		set_zhuashou_Angle(40.0f,300);    time_zhua += 350;
		delay_ms1((int)shengjiang_control(0,1000,200));
		

	}else if(task == 0x03){
		time_zhua += move_all(0.0f,1000,200   ,0,1000,200   ,70,11);
		time_zhua += move_all(0.0f,1000,200   ,35,1000,200   ,70,11);
		set_zhuashou_Angle_he();
		delay_ms1((int)shengjiang_control(0,1000,200));
		
		time_zhua += move_all(40,1000,200   ,0,1000,200   ,zhuanpan3[2],11);
		time_zhua += move_all(zhuanpan3[0],1000,200   ,0,1000,200   ,zhuanpan3[2],11);
		time_zhua += move_all(zhuanpan3[0],1000,200   ,zhuanpan3[1],1000,200   ,zhuanpan3[2],11);
		set_zhuashou_Angle(40.0f,300);    time_zhua += 350;
		delay_ms1((int)shengjiang_control(0,1000,200));
		
	}
}


void car_Init(void)
{
	delay_init(168);
	board_init();  //配置can总线协议
	LED_Init();  //配置LED指示灯
	OLED_Init();   //暂时不启用OLED //OLED中断和TIM5绑定在一起（两个必须同时用）
	Timer6_Init(); //delayms1的时钟
	PWM_Init();	  //使用定时器二，开启中断，实时控制舵机角度
	uart5_init(9600);
	uart6_init(115200);//串口屏用的UART6
	Serial_Init();	//通讯串口1初始化，用UART1
	Swith_Init();   //开关初始化
	imu_init();     //使用UART2
	PIDInit();		//用定时器实现定时中断//周期为50ms//该中断最好不要被别的中断打断
	Key_EXTI_Init();//按键中断//向地瓜派发送重启命令
    clear_ckp();    //清空串口屏
	dianji_move_flag = 1;//使能电机的运动
	TIM_SetCompare1(TIM3,0);  //关闭补光灯
}

//定时显示OLED和LCD显示屏
void TIM5_IRQHandler(void)
{
	if (TIM_GetITStatus(TIM5, TIM_IT_Update) == SET)
	{   
		imu_scan(fAcc, fGyro, fAngle);
		TIM_ClearITPendingBit(TIM5, TIM_IT_Update);
		OLED_ShowSignedNum(1,1,fAngle[2],3);
		OLED_ShowChar(1,5,'.');
		OLED_ShowNum(1,6,ABS((fAngle[2]-(int)fAngle[2])*1000),3);
		OLED_ShowSignedNum(2,1,angle,3);
		OLED_ShowChar(2,5,'.');
		OLED_ShowNum(2,6,ABS((angle-(int)angle)*1000),3);
		
	}
}

//与任务码相关联，放置的第一个物块定标用//第一轮放置1
void transfer_pi_position11(uint8_t task_num)
{   
	x_origin = (Serial_RxPacket[0]-0x30)*1000+(Serial_RxPacket[1]-0x30)*100+(Serial_RxPacket[2]-0x30)*10+(Serial_RxPacket[3]-0x30);
	y_origin = (Serial_RxPacket[4]-0x30)*1000+(Serial_RxPacket[5]-0x30)*100+(Serial_RxPacket[6]-0x30)*10+(Serial_RxPacket[7]-0x30);
	float x_center,y_center;//x加物块右移//y+物块下移
	if(Serial_RxPacket[8] == 0x31){
		x_center = x_center_red;y_center = y_center_red;
	}else if(Serial_RxPacket[8] == 0x32){
		x_center = x_center_green;y_center = y_center_green;
	}else if(Serial_RxPacket[8] == 0x33){
		x_center = x_center_blue;y_center = y_center_blue;
	}
	x_center =316;y_center =240;
	x_origin = x_origin - x_center;
	y_origin = y_origin - y_center;
	
	direct_x = x_origin * 1.1805555;    //实际尺寸系数
	direct_y = y_origin * 1.1805555;
	if(task_num == 2){
		if(Serial_RxPacket[8] == 0x32){
		}else if(Serial_RxPacket[8] == 0x31){
				direct_x = direct_x + distance_wukuai;
		}else if(Serial_RxPacket[8] == 0x33){
				direct_x = direct_x - distance_wukuai;
		}else if(Serial_RxPacket[8] == 0x34){
				direct_y = 3;direct_x = -3;
		}
	}else if(task_num == 1){
		if(Serial_RxPacket[8] == 0x31){
		}else if(Serial_RxPacket[8] == 0x32){
			direct_x = direct_x - distance_wukuai;
		}else if(Serial_RxPacket[8] == 0x33){
				direct_x = direct_x - 2*distance_wukuai;
		}else if(Serial_RxPacket[8] == 0x34){
				direct_y = 3;direct_x = -3;
		}
	}else if(task_num == 3){
		if(Serial_RxPacket[8] == 0x33){
		}else if(Serial_RxPacket[8] == 0x32){
			direct_x = direct_x + distance_wukuai;
		}else if(Serial_RxPacket[8] == 0x31){
				direct_x = direct_x + 2*distance_wukuai;
		}else if(Serial_RxPacket[8] == 0x34){
				direct_y = 3;direct_x = -3;
		}
	}
}


//与任务码相关联，放置的第一个物块定标用//第一轮放置2
void transfer_pi_position12(uint8_t task_num)
{   
	x_origin = (Serial_RxPacket[0]-0x30)*1000+(Serial_RxPacket[1]-0x30)*100+(Serial_RxPacket[2]-0x30)*10+(Serial_RxPacket[3]-0x30);
	y_origin = (Serial_RxPacket[4]-0x30)*1000+(Serial_RxPacket[5]-0x30)*100+(Serial_RxPacket[6]-0x30)*10+(Serial_RxPacket[7]-0x30);
	float x_center,y_center;//x加物块右移//y+物块下移
	if(Serial_RxPacket[8] == 0x31){
		x_center = x_center_red;y_center = y_center_red;
	}else if(Serial_RxPacket[8] == 0x32){
		x_center = x_center_green;y_center = y_center_green;
	}else if(Serial_RxPacket[8] == 0x33){
		x_center = x_center_blue;y_center = y_center_blue;
	}
	x_origin = x_origin - x_center;
	y_origin = y_origin - y_center;
	
	direct_x = x_origin * 0.29239766;    //实际尺寸系数
	direct_y = y_origin * 0.29239766;
	if(task_num == 2){
		if(Serial_RxPacket[8] == 0x32){
		}else if(Serial_RxPacket[8] == 0x31){
				direct_x = direct_x + distance_wukuai;
		}else if(Serial_RxPacket[8] == 0x33){
				direct_x = direct_x - distance_wukuai;
		}else if(Serial_RxPacket[8] == 0x34){
				direct_y = 3;direct_x = -3;
		}
	}else if(task_num == 1){
		if(Serial_RxPacket[8] == 0x31){
		}else if(Serial_RxPacket[8] == 0x32){
			direct_x = direct_x - distance_wukuai;
		}else if(Serial_RxPacket[8] == 0x33){
				direct_x = direct_x - 2*distance_wukuai;
		}else if(Serial_RxPacket[8] == 0x34){
				direct_y = 3;direct_x = -3;
		}
	}else if(task_num == 3){
		if(Serial_RxPacket[8] == 0x33){
		}else if(Serial_RxPacket[8] == 0x32){
			direct_x = direct_x + distance_wukuai;
		}else if(Serial_RxPacket[8] == 0x31){
				direct_x = direct_x + 2*distance_wukuai;
		}else if(Serial_RxPacket[8] == 0x34){
				direct_y = 3;direct_x = -3;
		}
	}
}

//代表圆盘中心检测
//只计算中心，不辨别颜色
void transfer_pi_position2(void)
{   
	x_origin = (Serial_RxPacket[0]-0x30)*1000+(Serial_RxPacket[1]-0x30)*100+(Serial_RxPacket[2]-0x30)*10+(Serial_RxPacket[3]-0x30);
	y_origin = (Serial_RxPacket[4]-0x30)*1000+(Serial_RxPacket[5]-0x30)*100+(Serial_RxPacket[6]-0x30)*10+(Serial_RxPacket[7]-0x30);
	float x_center,y_center;//x加物块右移//y+物块下移
	x_origin = x_origin - 300;
	y_origin = y_origin - 165;


	direct_x = x_origin * 0.5;    //实际尺寸系数
	direct_y = y_origin * 0.5;
	if(Serial_RxPacket[8] == 0x34){
		direct_y = 5;direct_x = -5;
	}
}

//与任务码相关联，放置的第一个物块定标用//第二轮放置
void transfer_pi_position3(uint8_t task_num)
{   
	x_origin = (Serial_RxPacket[0]-0x30)*1000+(Serial_RxPacket[1]-0x30)*100+(Serial_RxPacket[2]-0x30)*10+(Serial_RxPacket[3]-0x30);
	y_origin = (Serial_RxPacket[4]-0x30)*1000+(Serial_RxPacket[5]-0x30)*100+(Serial_RxPacket[6]-0x30)*10+(Serial_RxPacket[7]-0x30);
	float x_center,y_center;//x加物块右移//y+物块下移

	
	if(Serial_RxPacket[8] == 0x31){
		x_center = x_center_red;y_center = y_center_red ;
	}else if(Serial_RxPacket[8] == 0x32){
		x_center = x_center_green;y_center = y_center_green;
	}else if(Serial_RxPacket[8] == 0x33){
		x_center = x_center_blue;y_center = y_center_blue;
	}
	x_origin = x_origin - 310;
	y_origin = y_origin - 237;
	
	direct_x = x_origin * 0.96153846;    //实际尺寸系数
	direct_y = y_origin * 0.96153846;
	if(task_num == 2){
		if(Serial_RxPacket[8] == 0x32){
		}else if(Serial_RxPacket[8] == 0x31){
				direct_x = direct_x + distance_wukuai;
		}else if(Serial_RxPacket[8] == 0x33){
				direct_x = direct_x - distance_wukuai;
		}else if(Serial_RxPacket[8] == 0x34){
				direct_y = 5;direct_x = -5;
		}
	}else if(task_num == 1){
		if(Serial_RxPacket[8] == 0x31){
		}else if(Serial_RxPacket[8] == 0x32){
			direct_x = direct_x - distance_wukuai;
		}else if(Serial_RxPacket[8] == 0x33){
				direct_x = direct_x - 2*distance_wukuai;
		}else if(Serial_RxPacket[8] == 0x34){
				direct_y = 5;direct_x = -5;
		}
	}else if(task_num == 3){
		if(Serial_RxPacket[8] == 0x33){
		}else if(Serial_RxPacket[8] == 0x32){
			direct_x = direct_x + distance_wukuai;
		}else if(Serial_RxPacket[8] == 0x31){
				direct_x = direct_x + 2*distance_wukuai;
		}else if(Serial_RxPacket[8] == 0x34){
				direct_y = 5;direct_x = -5;
		}
	}
}

//与任务码相关联，放置的第一个物块定标用//第二轮放置
void transfer_pi_position4(uint8_t task_num)
{   
	x_origin = (Serial_RxPacket[0]-0x30)*1000+(Serial_RxPacket[1]-0x30)*100+(Serial_RxPacket[2]-0x30)*10+(Serial_RxPacket[3]-0x30);
	y_origin = (Serial_RxPacket[4]-0x30)*1000+(Serial_RxPacket[5]-0x30)*100+(Serial_RxPacket[6]-0x30)*10+(Serial_RxPacket[7]-0x30);
	float x_center,y_center;//x加物块右移//y+物块下移
	
	if(Serial_RxPacket[8] == 0x31){
		x_center = x_center_red  ;y_center = y_center_red;
	}else if(Serial_RxPacket[8] == 0x32){
		x_center = x_center_green;y_center = y_center_green;
	}else if(Serial_RxPacket[8] == 0x33){
		x_center = x_center_blue;y_center = y_center_blue;
	}
	x_origin = x_origin - 310;
	y_origin = y_origin - 237;
	
	direct_x = x_origin * 0.96153846;    //实际尺寸系数
	direct_y = y_origin * 0.96153846;
	if(task_num == 2){
		if(Serial_RxPacket[8] == 0x32){
		}else if(Serial_RxPacket[8] == 0x31){
				direct_x = direct_x + distance_wukuai -150;
		}
		}else if(Serial_RxPacket[8] == 0x32){
				direct_x = direct_x + distance_wukuai -150;
		}else if(Serial_RxPacket[8] == 0x33){
				direct_x = direct_x - distance_wukuai +150; //蓝色在中间
			
	}else if(task_num == 1){
		if(Serial_RxPacket[8] == 0x31){
		}else if(Serial_RxPacket[8] == 0x32){
			direct_x = direct_x - distance_wukuai;
		}else if(Serial_RxPacket[8] == 0x33){
				direct_x = direct_x - 2*distance_wukuai;
		}else if(Serial_RxPacket[8] == 0x34){
				direct_y = 5;direct_x = -5;
		}
	}else if(task_num == 3){
		if(Serial_RxPacket[8] == 0x33){
		}else if(Serial_RxPacket[8] == 0x32){
			direct_x = direct_x + distance_wukuai;
		}else if(Serial_RxPacket[8] == 0x31){
				direct_x = direct_x + 2*distance_wukuai;
		}else if(Serial_RxPacket[8] == 0x34){
				direct_y = 5;direct_x = -5;
		}
	}
}




/*
	先发送命令，等待一段时间如果还没有返回
	则继续发送，直到收到信息，立刻退出
*/
void wait_send_shumeipai(uint8_t message,uint16_t time)
{	
	Serial_GetRxFlag();//清空标志位
	Serial_SendByte(message);
	while(1){
		if(Serial_GetRxFlag() == 1){
			break;
		}
	}
}

void jixie_reset(void)
{	
	TIM_SetCompare1(TIM3,0);
	OLED_Clear();
	OLED_ShowString(8,1,"PL RES");
	while(swith_out() == 1){		
		LED_Toggle2();
		delay_ms1(50);
	}
	set_zhuashou_Angle(15.0f,300);
	delay_ms1((int)shengjiang_control(0,1000,200));
	move_all(0.0f,1000,200   ,0,1000,200   ,70.0f,11);
	set_wukuaipingtai(0x01);
	USART_ITConfig(USART2, USART_IT_RXNE, ENABLE);
	TIM_Cmd(TIM5, ENABLE); 
	OLED_Clear();
	OLED_ShowString(8,1,"RES ED");
	while(1){}
}
