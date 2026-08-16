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
#include "car.h"

void chusai(void);
void car_StartToPlate(void);
void car_StartToPlate_no(void);
void car_Start(void);
void car_ScanQR(void);
void car_GetWuLiao(void);
void car_GetWuLiao1(void);
void car_PlateToSeHuan1(void);
void car_SeHuan1Process(uint8_t TaskNum);
void car_SeHuan1ToSeHuan2(uint8_t TaskNum);

void car_SeHuan2ToPlate(void);
void car_Maduo(void);
void car_GoHome(void);
void car_ScanQR_test(void);
void set_shehuan(void);
void set_maduo(void);
void set_map(int a, int b);
void set_yuanpan(void); 

void car_SeHuan2Process(void);
void car_ScanQR_juesai(void);
void car_GetWuLiao_juesai(uint8_t TaskNum);
void car_SeHuan1ToSeHuan2_juesai(uint8_t TaskNum);
void car_SeHuan2ToPlate_juesai(uint8_t TaskNum);
void car_PlateToSehuan1_juesai(void);
void car_SeHuan2Process_juesai(uint8_t TaskNum);
void car_fangWuLiao_juesai(uint8_t TaskNum);
void car_GoHome_juesai(void);

void car_yuanliao_juesai(void);

//初赛所有的步骤都封装在里面了，直接在main里调用就行了
void chusai(void)
{
	/*====================初始化====================*/
	car_Init();
	
	/*====================启动====================*/
	car_StartToPlate();
	
	/*====================扫描二维码====================*/	
	car_ScanQR();
	
	/*====================第一次抓取物料====================*/
	car_GetWuLiao();
	
	/*====================第一次物料盘到粗加工====================*/
	car_PlateToSeHuan1();
	
	/*====================第一次粗加工====================*/
	car_SeHuan1Process(0);
	
	/*====================第一次粗加工到成品====================*/

	car_SeHuan1ToSeHuan2(0);
	
	/*====================第一次成品====================*/
	car_SeHuan2Process();
	
	/*====================成品到物料盘====================*/
	car_SeHuan2ToPlate();
	
	/*====================第二次抓取物料====================*/
	car_GetWuLiao1();
	
	/*====================第二次物料盘到粗加工====================*/
	car_PlateToSeHuan1();
	
	/*====================第二次粗加工====================*/
	car_SeHuan1Process(1);
	
	/*====================第二次粗加工到成品====================*/
	car_SeHuan1ToSeHuan2(1);
	
	/*====================第二次成品(码垛)====================*/
	car_Maduo();
	
	/*====================回家====================*/
	car_GoHome();
}

void juesai(void)
{
	/*====================初始化====================*/
	car_Init();
	
	/*====================启动====================*/
	car_StartToPlate(); //派+按键
	
	/*====================扫描二维码====================*/	
	car_ScanQR_juesai(); //移动到二维码，再移动到原料区
	
	/*====================第一次抓取物料====================*/
//	car_GetWuLiao_juesai(0);//码垛的识别+拿
	car_yuanliao_juesai();
	
	/*====================第一次物料环到粗加工环====================*/
	car_SeHuan1ToSeHuan2_juesai(0);
	
	
	/*====================第一次粗加工====================*/
	car_SeHuan2Process_juesai(0);
	
	/*====================第一次粗加工到成品====================*/
	car_SeHuan2ToPlate_juesai(0);
	
	
	/*====================第一次成品(到物料盘)====================*/
	car_fangWuLiao_juesai(0);
	
	/*====================成品到物料环====================*/
	car_PlateToSehuan1_juesai();
	
	/*====================第二次抓取物料====================*/
//	car_GetWuLiao_juesai(1);//码垛的识别+拿
	car_yuanliao_juesai();
	
	/*====================第二次物料环到粗加工环====================*/
	car_SeHuan1ToSeHuan2_juesai(1);
	
	/*====================第二次粗加工====================*/
	car_SeHuan2Process_juesai(1);
	
	/*====================第二次粗加工到成品====================*/
	car_SeHuan2ToPlate_juesai(1);
	
	/*====================第二次成品====================*/
	car_fangWuLiao_juesai(1);
	
	/*====================回家====================*/
	car_GoHome_juesai();
}


int main(void)
{		
	/*===================初赛一键启动====================*/	
//	chusai();
juesai();
	/*===================初赛一键启动====================*/

	
	/*====================调参数====================*/
//	set_yuanpan(); //设置色环：原地扫码、定位、拿色环
//	set_shehuan(); //设置色环：原地扫码、定位、放置色环
//	set_maduo(); //设置码垛，原地扫码、定位、放置色环
//	set_map(0,3); //跑图地图
	
	/*====================自定义调参====================*/
	
	car_Init();
	car_StartToPlate();		//派+按钮
	
	car_ScanQR_test();
	move_all(-70.0f,1000,200   ,0,1000,200   ,247,13);
	car_fangWuLiao_juesai(1);
//	car_yuanliao_juesai();
	jixie_reset();
	car_StartToPlate_no();	//按钮
	yuantai_fang0();
////	float zhuanpan0[3]={-71.0f , 20.0f , 247.0f};//转盘一号位
//float zhuanpan2[3]={90.0f  , 20.0f , 267.0f};//转盘二号位
	move_all(98.0f,1000,200   ,0,1000,200   ,267.5f,13);
	jixie_reset();
	car_GoHome_juesai();
	
	//亮度设置
//	TIM_SetCompare1(TIM3,200);
	
	//二维码测试
//	car_ScanQR(); 		//扫完码会移动
//	car_ScanQR_test();	//扫完码不会移动

	//通信测试
//	Serial_GetRxFlag();Serial_SendByte(0x32);

	//机械臂测试
//	move_all(0.0f,1000,200   ,0,1000,200    ,247,13);//
//	move_all(0.0f,1000,200   ,0,1000,200    ,70,13);//

	//勾爪测试
//	set_zhuashou_Angle_kai(); 	//开勾爪
//	set_zhuashou_Angle_he();	//关勾爪
	
	//物块平台测试
//	set_wukuaipingtai(0x01); 	//开勾爪
//	set_wukuaipingtai(0x02); 	//开勾爪
//	set_wukuaipingtai(0x03); 	//开勾爪

	//升降测试
//	delay_ms1((int)shengjiang_control(0,2000,240));

	//自转测试,最后一个参数越大越精准，越慢
//	mypid.integral = 0;PID_move(0,0,0,1000,90,0);//在原地旋转
//	PID_move(0,0,0,1000,90,3);
//	PID_move(0,0,0,1000,90,4);

	//移动测试
//	car_move2(150,0,150,150); 	//向开关为正方向移动
//	car_move1(0,-530,150,200);	//向地瓜派为正方向移动
//	car_move2(-150,0,150,150); 	//向机械臂为正方向移动
//	car_move1(0,530,150,200);	//向物料盘为正方向移动

	//所以机构复位到起始位置
//	jixie_reset();

}












void car_yuanliao_juesai(void)
{
	while(1){
		wait_send_shumeipai(0x68,10000);	
		transfer_pi_position4(0x02);
		car_move_distance(direct_x,direct_y,180,150);//至此第一次定标完成
		delay_ms1(200);
		if(Serial_RxPacket[8] != 0x34){
			break;
		}
	}
//	PID_move(0,0,0,1000,0,4);
		PID_move(0,0,0,1000,-180,4);
	{
		wait_send_shumeipai(0x68,10000);		
		transfer_pi_position4(0x02);	
		if(Serial_RxPacket[8] == 0x34){
			car_move_distance(0,0,70,50);
		}else{	
			car_move_distance(direct_x,direct_y,180,150);//至此第二次定标完成
		}
	}
	
	/*====================第一次粗加工拿s====================*/
	
	wait_send_shumeipai(0x69,20000);
	ypcode[0]= Serial_RxPacket[0]-0x30;ypcode[1] = Serial_RxPacket[1]-0x30;ypcode[2] = Serial_RxPacket[2]-0x30;

	
	set_wukuaipingtai(0x01);
	//拿一
	set_zhuashou_Angle_kai();
	na(ypcode[0]);
	
	set_wukuaipingtai(0x02);
	//拿二
	na(ypcode[1]);
	set_wukuaipingtai(0x03);
	//拿三
	na(ypcode[2]);
	//复位到识别的位置
	set_wukuaipingtai(0x01);
	
	
	move_all(-70.0f,1000,200   ,0,1000,200    ,247,13);//近识别位
	/*====================第一次粗加工拿e====================*/

}


/*====================启动====================*/
void car_Start(void)
{
	while(swith_out() == 1){		
		LED_Toggle2();
		delay_ms1(50);
		// 简单方法：直接显示
		OLED_ShowString(12, 1, "OK");
	}//地瓜派已经准备好，按下开关即可启动
	mypid.integral = 0;
	WHT101_ANGLEZCali();//101z轴置零
}

void car_StartToPlate(void)
{
	while(1){
		LED_Toggle2();
		delay_ms1(500);
		// 简单方法：直接显示
		if((Serial_RxPacket[0]==0x39) && (Serial_RxPacket[1]==0x38)){
			break;
	    }
		
	}

	while(swith_out() == 1){		
		LED_Toggle2();
		delay_ms1(50);
		// 简单方法：直接显示
		OLED_ShowString(12, 1, "OK");
	}//地瓜派已经准备好，按下开关即可启动
	mypid.integral = 0;
	WHT101_ANGLEZCali();//101z轴置零
}

void car_StartToPlate_no(void)
{

	while(swith_out() == 1){		
		LED_Toggle2();
		delay_ms1(50);
		// 简单方法：直接显示
		OLED_ShowString(12, 1, "OK");
	}//地瓜派已经准备好，按下开关即可启动
	mypid.integral = 0;
	WHT101_ANGLEZCali();//101z轴置零
}

/*====================扫描二维====================*/	
void car_ScanQR_juesai(void)
{
		//扫二维码
	Serial_GetRxFlag();Serial_SendByte(0x31);
	map(0,1);
	//读取地瓜派信息	
	while(1){
		if (Serial_GetRxFlag() == 1){   //收到数据包
			   sprintf(tjcstr, "t0.txt=\"%d%d%d+%d%d%d \"",
										Serial_RxPacket[0]-0x30,Serial_RxPacket[1]-0x30,Serial_RxPacket[2]-0x30,
										Serial_RxPacket[4]-0x30,Serial_RxPacket[5]-0x30,Serial_RxPacket[6]-0x30);
				HMISends(tjcstr);
				HMISendb(0xff);//在显示屏上面显示任务
				break;
			  }
	}	
	task[0]= Serial_RxPacket[0]-0x30;task[1] = Serial_RxPacket[1]-0x30;task[2] = Serial_RxPacket[2]-0x30;
	task[3]= Serial_RxPacket[4]-0x30;task[4] = Serial_RxPacket[5]-0x30;task[5] = Serial_RxPacket[6]-0x30;
	
	set_zhuashou_Angle(40.0f,300);
	move_all(-70.0f,1000,200   ,0,1000,200   ,247,13);
	
	map(1,5);
	TIM_SetCompare1(TIM3,200);
//	Serial_GetRxFlag();Serial_SendByte(0x39);
}

void car_ScanQR(void)
{
		//扫二维码
	Serial_GetRxFlag();Serial_SendByte(0x31);
	//移动到地图正上方
	car_move2(150,0,150,150);
	car_move1(0,-1035,150,200);
	//读取地瓜派信息	
	while(1){
		if (Serial_GetRxFlag() == 1){   //收到数据包
			   sprintf(tjcstr, "t0.txt=\"%d%d%d+%d%d%d \"",
										Serial_RxPacket[0]-0x30,Serial_RxPacket[1]-0x30,Serial_RxPacket[2]-0x30,
										Serial_RxPacket[4]-0x30,Serial_RxPacket[5]-0x30,Serial_RxPacket[6]-0x30);
				HMISends(tjcstr);
				HMISendb(0xff);//在显示屏上面显示任务
				break;
			  }
	}	
	task[0]= Serial_RxPacket[0]-0x30;task[1] = Serial_RxPacket[1]-0x30;task[2] = Serial_RxPacket[2]-0x30;
	task[3]= Serial_RxPacket[4]-0x30;task[4] = Serial_RxPacket[5]-0x30;task[5] = Serial_RxPacket[6]-0x30;
	
	set_zhuashou_Angle(40.0f,300);
	move_all(-70.0f,1000,200   ,0,1000,200   ,247,13);
	
	TIM_SetCompare1(TIM3,200);

	car_move1(0,-1000+100,150,200);
	car_move2(-10,0,100,100);
	Serial_GetRxFlag();Serial_SendByte(0x32);
	move_all(85.0f,1000,200   ,0,1000,200   ,247,13);
}

void car_ScanQR_test(void)
{
		//扫二维码
	Serial_GetRxFlag();Serial_SendByte(0x31);
//	car_move2(150,0,150,150);
//	car_move1(0,-530,150,200);
	//读取地瓜派信息	
	while(1){
		if (Serial_GetRxFlag() == 1){   //收到数据包
			   sprintf(tjcstr, "t0.txt=\"%d%d%d+%d%d%d \"",
										Serial_RxPacket[0]-0x30,Serial_RxPacket[1]-0x30,Serial_RxPacket[2]-0x30,
										Serial_RxPacket[4]-0x30,Serial_RxPacket[5]-0x30,Serial_RxPacket[6]-0x30);
				HMISends(tjcstr);
				HMISendb(0xff);//在显示屏上面显示任务
				break;
			  }
	}	
	task[0]= Serial_RxPacket[0]-0x30;task[1] = Serial_RxPacket[1]-0x30;task[2] = Serial_RxPacket[2]-0x30;
	task[3]= Serial_RxPacket[4]-0x30;task[4] = Serial_RxPacket[5]-0x30;task[5] = Serial_RxPacket[6]-0x30;
	
	set_zhuashou_Angle(40.0f,300);

	
	TIM_SetCompare1(TIM3,200);
//	car_move1(0,-1000+90,150,200);

}

void car_GetWuLiao(void)
{
	while(1){
		while(1){
			if(Serial_GetRxFlag() == 1){
				break;
			}
		}
		transfer_pi_position2();
		car_move_distance(direct_x,direct_y,100,80);//至此第一次定标完成
		wait_send_shumeipai(0x32,15000);

		if(Serial_RxPacket[8] != 0x34){
			break;
		}else{
			wait_send_shumeipai(0x32,15000);
		}	
	}
	
	wait_send_shumeipai(0x33,20000);
	ypcode[0]= Serial_RxPacket[0]-0x30;ypcode[1] = Serial_RxPacket[1]-0x30;ypcode[2] = Serial_RxPacket[2]-0x30;
	
	//拿走第一个物块
	yuantai_na(ypcode[0]);
	move_all(0.0f,1000,200   ,0,1000,200  ,70,12);

	set_wukuaipingtai_Angle(20.0f+124.0f,300);
	

	//拿走第二个物块
	yuantai_na1(ypcode[1]);

	wait_send_shumeipai(0x35,30000);
	while(1){
		if(Serial_RxPacket[0] == 0x39 && Serial_RxPacket[1] == 0x38){
			break;
		}
	}Serial_RxPacket[0] = 0x30;Serial_RxPacket[1] = 0x30;
	
	yuantai_na2(ypcode[1]);
	set_wukuaipingtai(0x03);
	
	//拿走第三个物块
	yuantai_na1(ypcode[2]); 
	
	wait_send_shumeipai(0x36,30000);
	while(1){
		if(Serial_RxPacket[0] == 0x39 && Serial_RxPacket[1] == 0x38){
			break;
		}
	}Serial_RxPacket[0] = 0x30;Serial_RxPacket[1] = 0x30;	
	
	yuantai_na2(ypcode[2]);

	TIM_SetCompare1(TIM3,0);
	//复位到识别的位置
	set_zhuashou_Angle(45.0f,200);
	move_all(-70.0f,1000,200   ,0,1000,200    ,247,13);//转过来识别
	set_wukuaipingtai(0x01);
	
}

void car_GetWuLiao1(void)
{
	while(1){
		while(1){
			if(Serial_GetRxFlag() == 1){
				break;
			}
		}
		transfer_pi_position2();
		car_move_distance(direct_x,direct_y,100,80);//至此第一次定标完成
		wait_send_shumeipai(0x32,15000);

		if(Serial_RxPacket[8] != 0x34){
			break;
		}else{
			wait_send_shumeipai(0x61,15000);
		}	
	}

	move_all(85.0f,1000,200   ,0,1000,200   ,244,10);
	wait_send_shumeipai(0x34,20000);
	ypcode[0]= Serial_RxPacket[0]-0x30;ypcode[1] = Serial_RxPacket[1]-0x30;ypcode[2] = Serial_RxPacket[2]-0x30;
	
	//拿走第一个物块
	yuantai_na(ypcode[0]);
	move_all(0.0f,1000,200   ,0,1000,200   ,70,13);
	set_wukuaipingtai_Angle(20.0f+124.0f,300);
	

	//拿走第二个物块
	yuantai_na1(ypcode[1]);

	wait_send_shumeipai(0x62,30000);
	while(1){
		if(Serial_RxPacket[0] == 0x39 && Serial_RxPacket[1] == 0x38){
			break;
		}
	}Serial_RxPacket[0] = 0x30;Serial_RxPacket[1] = 0x30;
	
	yuantai_na2(ypcode[1]);
	set_wukuaipingtai(0x03);
	
	//拿走第三个物块
	yuantai_na1(ypcode[2]); 
	
	wait_send_shumeipai(0x63,30000);
	while(1){
		if(Serial_RxPacket[0] == 0x39 && Serial_RxPacket[1] == 0x38){
			break;
		}
	}Serial_RxPacket[0] = 0x30;Serial_RxPacket[1] = 0x30;	
	
	yuantai_na2(ypcode[2]);

	TIM_SetCompare1(TIM3,0);
	//复位到识别的位置
	
	set_zhuashou_Angle(45.0f,200);
	move_all(-70.0f,1000,200   ,0,1000,200    ,247,13);//转过来识别
	set_wukuaipingtai(0x01);
	
}

//决赛放物块到转盘上
void car_fangWuLiao_juesai(uint8_t TaskNum)
{
	if(TaskNum ==0){
			Serial_GetRxFlag();Serial_SendByte(0x32);
		}else if(TaskNum ==1){
			Serial_GetRxFlag();Serial_SendByte(0x61);
		}
	
	while(1){
		while(1){
			if(Serial_GetRxFlag() == 1){
				break;
			}
		}
		transfer_pi_position2();
		car_move_distance(direct_x,direct_y,100,80);//至此第一次定标完成

		
		if(Serial_RxPacket[8] != 0x34){
			break;
		}else{
			if(TaskNum ==0){
			Serial_GetRxFlag();Serial_SendByte(0x32);
			}else{
			Serial_GetRxFlag();Serial_SendByte(0x61);
		}
		}	
	}
	
	//定位之后先拿一个物块在手上，之后看顺序
	yuantai_fang0();
//	move_all(85.0f,1000,200   ,0,1000,200   ,244,10);
	if(TaskNum ==0){
			wait_send_shumeipai(0x33,15000);
		}else if(TaskNum ==1){
			wait_send_shumeipai(0x34,15000);
		}
	
	ypcode[0]= Serial_RxPacket[0]-0x30;ypcode[1] = Serial_RxPacket[1]-0x30;ypcode[2] = Serial_RxPacket[2]-0x30;
	
	//拿走第一个物块
	yuantai_fang(ypcode[0]);
	set_wukuaipingtai_Angle(20.0f+124.0f,300);
	

	//拿走第二个物块
	yuantai_fang1(ypcode[1]);

	if(TaskNum ==0){
			wait_send_shumeipai(0x35,15000);
		}else if(TaskNum ==1){
			wait_send_shumeipai(0x62,15000);
		}
	
	while(1){
		if(Serial_RxPacket[0] == 0x39 && Serial_RxPacket[1] == 0x38){
			break;
		}
	}Serial_RxPacket[0] = 0x30;Serial_RxPacket[1] = 0x30;
	
	yuantai_fang2(ypcode[1]);
	set_wukuaipingtai(0x03);
	
	//拿走第三个物块
	yuantai_fang1(ypcode[2]); 
	
	if(TaskNum ==0){
			wait_send_shumeipai(0x36,15000);
		}else if(TaskNum ==1){
			wait_send_shumeipai(0x63,15000);
		}
	while(1){
		if(Serial_RxPacket[0] == 0x39 && Serial_RxPacket[1] == 0x38){
			break;
		}
	}Serial_RxPacket[0] = 0x30;Serial_RxPacket[1] = 0x30;	
	
	yuantai_fang2(ypcode[2]);

	TIM_SetCompare1(TIM3,0);
	//复位到识别的位置
	set_zhuashou_Angle(45.0f,200);
	move_all(-70.0f,1000,200   ,0,1000,200    ,247,13);//转过来识别
	set_wukuaipingtai(0x01);
	
}

void car_PlateToSeHuan1(void)
{
			//到粗加工区
	PID_move(-30,0,0,400,0,1);//回倒车
	delay_ms1(200);
	car_move1(0,400,150,200);
	
	mypid.integral = 0;PID_move(0,0,0,1000,90,0);//在原地旋转
	PID_move(0,0,0,1000,90,3);
	
	car_move1(0,-1700,200,200);//快速通过
	
	mypid.integral = 0;PID_move(0,0,0,1000,-180,0);//在粗加工区原地旋转
	TIM_SetCompare1(TIM3,500);  //关闭补光灯
	PID_move(0,0,0,1000,-180,3);
	
}

void car_SeHuan1Process(uint8_t TaskNum)
{
	/*====================第一次粗加工s====================*/
	move_all(-70.0f,1000,200   ,0,1000,200    ,247,13);//转过来识别
	
	while(1){
		wait_send_shumeipai(0x37,10000);//如果发送了信息，但是一直没有得到回应，那么就一直发送
		transfer_pi_position11(0x02);
		car_move_distance(direct_x,direct_y,180,150);
		if(Serial_RxPacket[8] != 0x34){
			break;
		}
		//如果返回了没看到的信息，那就微微调整一下，再重复给地瓜派发送
		//反之如果返回了看到的信息（也即第九位并非0x34）,则可以退出该程序
	}

	//角度校正
//	PID_move(0,0,0,1000,0.0f,4);//-180.0改为0
	PID_move(0,0,0,1000,-180.0f,4);//-180.0改为0
	delay_ms1(500);
	
	
	//精细定标
	{
		wait_send_shumeipai(0x38,10000);//如果发送了信息，但是一直没有得到回应，那么就一直发送
		transfer_pi_position12(0x02);	
		if(Serial_RxPacket[8] == 0x34){
			car_move_distance(0,0,70,50);//如果没有看到颜色，那就不移动
		}else{	
			car_move_distance(direct_x,direct_y,130,100);//如果看到颜色，那就按照正常的方式移动
		}
	}//至此第二次定标完成
	
	
//*************************1.4.1Start第三部分，放**********************//
	set_zhuashou_Angle_kai();
	move_all(0.0f,1000,200   ,20,1000,200   ,70,13);//复位
	move_all(0.0f,1000,200   ,35,1000,200   ,70,13);//物块平台抓物块
	set_zhuashou_Angle_he();
	//放置第一个
	fangzhi(task[0+(TaskNum)*3]);

	set_wukuaipingtai_Angle(143.0f,300);
	delay_ms1((int)shengjiang_control(20,2000,240));
	move_all(0.0f,1000,200   ,20,1000,200   ,70,13);//复位
	move_all(0.0f,1000,200   ,35,1000,200   ,70,13);//物块平台抓物块
	set_zhuashou_Angle_he();
	
	//放置第二个	
	fangzhi(task[1+(TaskNum)*3]);
	
	set_wukuaipingtai_Angle(258.0f,300);
	delay_ms1((int)shengjiang_control(20,2000,240));
	move_all(0.0f,1000,200   ,20,1000,200   ,70,13);//复位
	move_all(0.0f,1000,200   ,35,1000,200   ,70,13);//物块平台抓物块
	set_zhuashou_Angle_he();
	
	//放置第三个	
	fangzhi(task[2+(TaskNum)*3]);
	//复位到识别的位置
	set_wukuaipingtai(0x01);
	set_zhuashou_Angle_kai();
	/*====================第一次粗加工放e====================*/


	/*====================第一次粗加工拿s====================*/
	delay_ms1((int)shengjiang_control(70,2000,240));//复位
	
	
	
	set_wukuaipingtai(0x01);
	//拿一
	set_zhuashou_Angle_kai();
	na(task[0+(TaskNum)*3]);
	
	set_wukuaipingtai_Angle(143.0f,300);
	//拿二
	na(task[1+(TaskNum)*3]);
	set_wukuaipingtai_Angle(258.0f,300);
	//拿三
	na(task[2+(TaskNum)*3]);
	//复位到识别的位置
	set_wukuaipingtai(0x01);
	
	move_all(-70.0f,1000,200   ,0,1000,200    ,247,13);//转过来识别
	/*====================第一次粗加工拿e====================*/
	/*====================第一次粗加工e====================*/
}

void car_SeHuan2Process_juesai(uint8_t TaskNum)
{
	/*====================第一次粗加工s====================*/
	move_all(-70.0f,1000,200   ,0,1000,200    ,247,13);//转过来识别
	
	while(1){
		wait_send_shumeipai(0x37,10000);//如果发送了信息，但是一直没有得到回应，那么就一直发送
		transfer_pi_position11(0x02);
		car_move_distance(direct_x,direct_y,180,150);
		if(Serial_RxPacket[8] != 0x34){
			break;
		}
		//如果返回了没看到的信息，那就微微调整一下，再重复给地瓜派发送
		//反之如果返回了看到的信息（也即第九位并非0x34）,则可以退出该程序
	}

	//角度校正
//	PID_move(0,0,0,1000,0.0f,4);//-180.0改为0
	PID_move(0,0,0,1000,90.0f,4);
	delay_ms1(500);
	
	
	//精细定标
	{
		wait_send_shumeipai(0x38,10000);//如果发送了信息，但是一直没有得到回应，那么就一直发送
		transfer_pi_position12(0x02);	
		if(Serial_RxPacket[8] == 0x34){
			car_move_distance(0,0,70,50);//如果没有看到颜色，那就不移动
		}else{	
			car_move_distance(direct_x,direct_y,130,100);//如果看到颜色，那就按照正常的方式移动
		}
	}//至此第二次定标完成
	
	
//*************************1.4.1Start第三部分，放**********************//
	set_zhuashou_Angle_kai();
	move_all(0.0f,1000,200   ,20,1000,200   ,70,13);//复位
	move_all(0.0f,1000,200   ,35,1000,200   ,70,13);//物块平台抓物块
	set_zhuashou_Angle_he();
	//放置第一个
	fangzhi(task[0+(TaskNum)*3]);

	set_wukuaipingtai_Angle(143.0f,300);
	delay_ms1((int)shengjiang_control(20,2000,240));
	move_all(0.0f,1000,200   ,20,1000,200   ,70,13);//复位
	move_all(0.0f,1000,200   ,35,1000,200   ,70,13);//物块平台抓物块
	set_zhuashou_Angle_he();
	
	//放置第二个	
	fangzhi(task[1+(TaskNum)*3]);
	
	set_wukuaipingtai_Angle(258.0f,300);
	delay_ms1((int)shengjiang_control(20,2000,240));
	move_all(0.0f,1000,200   ,20,1000,200   ,70,13);//复位
	move_all(0.0f,1000,200   ,35,1000,200   ,70,13);//物块平台抓物块
	set_zhuashou_Angle_he();
	
	//放置第三个	
	fangzhi(task[2+(TaskNum)*3]);
	//复位到识别的位置
	set_wukuaipingtai(0x01);
	set_zhuashou_Angle_kai();
	/*====================第一次粗加工放e====================*/


	/*====================第一次粗加工拿s====================*/
	delay_ms1((int)shengjiang_control(70,2000,240));//复位
	
	
	
	set_wukuaipingtai(0x01);
	//拿一
	set_zhuashou_Angle_kai();
	na(task[0+(TaskNum)*3]);
	
	set_wukuaipingtai_Angle(143.0f,300);
	//拿二
	na(task[1+(TaskNum)*3]);
	set_wukuaipingtai_Angle(258.0f,300);
	//拿三
	na(task[2+(TaskNum)*3]);
	//复位到识别的位置
	set_wukuaipingtai(0x01);
	
	move_all(-70.0f,1000,200   ,0,1000,200    ,247,13);//转过来识别
	/*====================第一次粗加工拿e====================*/
	/*====================第一次粗加工e====================*/
}



void car_SeHuan1ToSeHuan2(uint8_t TaskNum)
{
	PID_move(-30,0,0,300,-180,1);//在粗加工区回退
	PID_move(0,0,0,500,-180,3);
	car_move1(140,140+680,180,180);//从绿色出发
	delay_ms1(100);
	
	mypid.integral = 0;PID_move(0,0,0,1000,90,0);

	
	car_move1(0,140+645,180,150);
	TIM_SetCompare1(TIM3,500);  //关闭补光灯
}

void car_SeHuan1ToSeHuan2_juesai(uint8_t TaskNum)
{
	PID_move(-30,0,0,300,-180,1);//在粗加工区回退
	PID_move(0,0,0,500,-180,3);
	car_move1(140,140+680,180,180);//从绿色出发
	delay_ms1(100);
	
	mypid.integral = 0;PID_move(0,0,0,1000,90,0);

	car_move1(0,140+645,180,150);
	TIM_SetCompare1(TIM3,300);  //关闭补光灯
}

void car_SeHuan2Process(void)
{
	while(1){
		wait_send_shumeipai(0x37,15000);
		transfer_pi_position11(0x02);
		car_move_distance(direct_x,direct_y,180,150);
		if(Serial_RxPacket[8] != 0x34){
			break;
		}
		//如果返回了没看到的信息，那就微微调整一下，再重复给地瓜派发送
		//反之如果返回了看到的信息（也即第九位并非0x34）,则可以退出该程序
	}

	//角度校正
	wait_send_shumeipai(0x64,10000);
	angle = (Serial_RxPacket[7]-0x30) + (Serial_RxPacket[8]-0x30)*0.1f;
	if(ABS(angle) >= 2.0f){
		angle = 2.0f;
	}
	if((Serial_RxPacket[6]-0x30) == 0){
		angle = -angle;
	}
	PID_move(0,0,0,1000,90-angle,4);
	
	//精细定标
	{
		wait_send_shumeipai(0x38,10000);//如果发送了信息，但是一直没有得到回应，那么就一直发送
		transfer_pi_position12(0x02);	
		if(Serial_RxPacket[8] == 0x34){
			car_move_distance(0,0,70,50);//如果没有看到颜色，那就不移动
		}else{	
			car_move_distance(direct_x,direct_y,130,100);//如果看到颜色，那就按照正常的方式移动
		}
	}//至此第二次定标完成

//*************************1.6.1Start第三部分，放**********************//
	set_zhuashou_Angle_kai();
	move_all(0.0f,1000,200   ,0,1000,200   ,70,13);//复位
	move_all(0.0f,1000,200   ,35,1000,200   ,70,13);//物块平台抓物块
	set_zhuashou_Angle_he();
	//放置第一个
	fangzhi(task[0]);
//	jixie_reset();
	set_wukuaipingtai_Angle(143.0f,300);
	delay_ms1((int)shengjiang_control(0,2000,240));
	move_all(0.0f,1000,200   ,0,1000,200   ,70,13);//复位
	move_all(0.0f,1000,200   ,35,1000,200   ,70,13);//物块平台抓物块
	set_zhuashou_Angle_he();
	
	//放置第二个	
	fangzhi(task[1]);
	
	set_wukuaipingtai_Angle(258.0f,300);
	delay_ms1((int)shengjiang_control(0,2000,240));
	move_all(0.0f,1000,200   ,0,1000,200   ,70,13);//复位
	move_all(0.0f,1000,200   ,35,1000,200   ,70,13);//物块平台抓物块
	set_zhuashou_Angle_he();
	
	//放置第三个	
	fangzhi(task[2]);
	//复位到识别的位置
	set_wukuaipingtai(0x01);
	set_zhuashou_Angle_kai();
	delay_ms1((int)shengjiang_control(0,2000,240));
	move_all(-30.0f,1000,200   ,0,1000,200    ,247,13);//转过来识别
}

void car_SeHuan2ToPlate(void)
{
	PID_move(-30,0,0,300,90,1);//回退
	delay_ms1(100);
	//回到原料
	car_move1(140,220+650,180,180);//从绿色出发
	
	mypid.integral = 0;PID_move(0,0,0,1000,0,0);
	
	car_move1(140,370,180,180);
	move_all1(85.0f,1000,200   ,0,1000,200   ,247,13);
	PID_move(30,0,0,300,0,1);//在粗加工区往前靠
	TIM_SetCompare1(TIM3,500);  //关闭补光灯
	Serial_GetRxFlag();Serial_SendByte(0x61);
	delay_ms1(100);	
}

void car_SeHuan2ToPlate_juesai(uint8_t TaskNum)
{
	map(3,4);
	TIM_SetCompare1(TIM3,500);  //关闭补光灯
	delay_ms1(100);	
}

void car_GetWuLiao_juesai(uint8_t TaskNum)
{
	while(1){
		wait_send_shumeipai(0x39,10000);	
		transfer_pi_position3(0x02);
		car_move_distance(direct_x,direct_y,180,150);//至此第一次定标完成
		delay_ms1(200);
		if(Serial_RxPacket[8] != 0x34){
			break;
		}
	}
	PID_move(0,0,0,1000,-180,4);
	{
		wait_send_shumeipai(0x39,10000);		
		transfer_pi_position3(0x02);	
		if(Serial_RxPacket[8] == 0x34){
			car_move_distance(0,0,70,50);
		}else{	
			car_move_distance(direct_x,direct_y,180,150);//至此第二次定标完成
		}
	}
	/*====================第一次粗加工拿s====================*/
	set_wukuaipingtai(0x01);
	//拿一
	set_zhuashou_Angle_kai();
	na(task[0+(TaskNum)*3]);
	
	set_wukuaipingtai(0x02);
	//拿二
	na(task[1+(TaskNum)*3]);
	set_wukuaipingtai(0x03);
	//拿三
	na(task[2+(TaskNum)*3]);
	//复位到识别的位置
	set_wukuaipingtai(0x01);
	
	move_all(-70.0f,1000,200   ,0,1000,200    ,247,13);//近识别位
	/*====================第一次粗加工拿e====================*/

}

void car_PlateToSehuan1_juesai(void)
{
	car_move2(60,0,150,150);
	map(4,5);

}

void car_Maduo(void)
{
	while(1){
		wait_send_shumeipai(0x39,10000);	
		transfer_pi_position3(0x02);
		car_move_distance(direct_x,direct_y,180,150);//至此第一次定标完成
		delay_ms1(200);
		if(Serial_RxPacket[8] != 0x34){
			break;
		}
	}
	PID_move(0,0,0,1000,90,4);
	{
		wait_send_shumeipai(0x39,10000);		
		transfer_pi_position3(0x02);	
		if(Serial_RxPacket[8] == 0x34){
			car_move_distance(0,0,70,50);
		}else{	
			car_move_distance(direct_x,direct_y,180,150);//至此第二次定标完成
		}
	}
	set_zhuashou_Angle_kai();
	move_all(0.0f,1000,200   ,0,1000,200   ,70,13);//物块平台抓物块
	move_all(0.0f,1000,200   ,30,1000,200   ,70,13);//物块平台抓物块
	set_zhuashou_Angle_he();
	//放置第一个
	
	fangzhi_maduo(task[3]);
	
	

	set_zhuashou_Angle(45.0f,200);
	delay_ms1((int)shengjiang_control(0,2000,240));
	
	set_wukuaipingtai(0x02);
	delay_ms1((int)shengjiang_control(0,2000,240));
	move_all(0.0f,1000,200   ,30,1000,200   ,70,13);//物块平台抓物块
	set_zhuashou_Angle_he();
	
	//放置第二个	
	fangzhi_maduo(task[4]);
	
	set_wukuaipingtai(0x03);
	delay_ms1((int)shengjiang_control(0,2000,240));
	
	move_all(0.0f,1000,200   ,30,1000,200   ,70,13);//物块平台抓物块
	set_zhuashou_Angle_he();
	
	//放置第三个	
	fangzhi_maduo(task[5]);
	set_wukuaipingtai(0x01);
}

void car_GoHome(void)
{
	PID_move(-30,0,0,300,90,1);//回退
	move_all(0.0f,1000,200   ,0,1000,200   ,70,13);
	car_move1(140,220+650,180,180);//从绿色出发
	mypid.integral = 0;PID_move(0,0,0,1300,0,0);
	delay_ms1(500); 
	
	car_move1(140,2000-180,200,200);
	car_move2(-170,0,150,150);//在粗加工区往前靠
	jixie_reset();
}

void car_GoHome_juesai(void)
{
	map(5,0);
	jixie_reset();
}

void clear_ckp(void)
{
	sprintf(tjcstr, "t0.txt=\"  \"");
			HMISends(tjcstr);
	        HMISendb(0xff);//在显示屏上面显示任务
}

void set_shehuan(void)
{
	/*====================初始化====================*/
	car_Init();
	
	/*====================启动====================*/
	car_StartToPlate();
	car_ScanQR_test();
	
	move_all(-70.0f,1000,200   ,0,1000,200    ,247,13);//转过来识别
	
	/*====================第一次粗加工s====================*/
	move_all(-70.0f,1000,200   ,0,1000,200    ,247,13);//转过来识别
	
	while(1){
		wait_send_shumeipai(0x37,10000);//如果发送了信息，但是一直没有得到回应，那么就一直发送
		transfer_pi_position11(0x02);
		car_move_distance(direct_x,direct_y,180,150);
		if(Serial_RxPacket[8] != 0x34){
			break;
		}
		//如果返回了没看到的信息，那就微微调整一下，再重复给地瓜派发送
		//反之如果返回了看到的信息（也即第九位并非0x34）,则可以退出该程序
	}

	//角度校正
	PID_move(0,0,0,1000,0.0f,4);//-180.0改为0
//	PID_move(0,0,0,1000,-180.0f,4);//-180.0改为0
	delay_ms1(500);
	
	
	//精细定标
	{
		wait_send_shumeipai(0x38,10000);//如果发送了信息，但是一直没有得到回应，那么就一直发送
		transfer_pi_position12(0x02);	
		if(Serial_RxPacket[8] == 0x34){
			car_move_distance(0,0,70,50);//如果没有看到颜色，那就不移动
		}else{	
			car_move_distance(direct_x,direct_y,130,100);//如果看到颜色，那就按照正常的方式移动
		}
	}//至此第二次定标完成
	
	
	
	
//*************************1.4.1Start第三部分，放**********************//
	set_zhuashou_Angle_kai();
	move_all(0.0f,1000,200   ,20,1000,200   ,70,13);//复位
	move_all(0.0f,1000,200   ,35,1000,200   ,70,13);//物块平台抓物块
	set_zhuashou_Angle_he();
	//放置第一个
	fangzhi(task[0]);

	set_wukuaipingtai_Angle(143.0f,300);
	delay_ms1((int)shengjiang_control(20,2000,240));
	move_all(0.0f,1000,200   ,20,1000,200   ,70,13);//复位
	move_all(0.0f,1000,200   ,35,1000,200   ,70,13);//物块平台抓物块
	set_zhuashou_Angle_he();
	
	//放置第二个	
	fangzhi(task[1]);
	
	set_wukuaipingtai_Angle(258.0f,300);
	delay_ms1((int)shengjiang_control(20,2000,240));
	move_all(0.0f,1000,200   ,20,1000,200   ,70,13);//复位
	move_all(0.0f,1000,200   ,35,1000,200   ,70,13);//物块平台抓物块
	set_zhuashou_Angle_he();
	
	//放置第三个	
	fangzhi(task[2]);
	//复位到识别的位置
	set_wukuaipingtai(0x01);
	set_zhuashou_Angle_kai();
	jixie_reset();
	/*====================第一次粗加工放e====================*/
	
}

void set_yuanpan(void)
{
	/*====================初始化====================*/
	car_Init();
	
	/*====================启动====================*/
	car_StartToPlate();
	car_ScanQR_test();
	
	move_all(-70.0f,1000,200   ,0,1000,200    ,247,13);//转过来识别
	Serial_GetRxFlag();Serial_SendByte(0x32);
	while(1){
		while(1){
			if(Serial_GetRxFlag() == 1){
				break;
			}
		}
		transfer_pi_position2();
		car_move_distance(direct_x,direct_y,100,80);//至此第一次定标完成
		wait_send_shumeipai(0x32,15000);

		if(Serial_RxPacket[8] != 0x34){
			break;
		}else{
			wait_send_shumeipai(0x32,15000);
		}	
	}
	
	wait_send_shumeipai(0x33,20000);
	ypcode[0]= Serial_RxPacket[0]-0x30;ypcode[1] = Serial_RxPacket[1]-0x30;ypcode[2] = Serial_RxPacket[2]-0x30;
	
	//拿走第一个物块
	yuantai_na(ypcode[0]);
	move_all(0.0f,1000,200   ,0,1000,200  ,70,12);

	set_wukuaipingtai_Angle(20.0f+124.0f,300);
	

	//拿走第二个物块
	yuantai_na1(ypcode[1]);
	
	wait_send_shumeipai(0x35,30000);
	while(1){
		if(Serial_RxPacket[0] == 0x39 && Serial_RxPacket[1] == 0x38){
			break;
		}
	}Serial_RxPacket[0] = 0x30;Serial_RxPacket[1] = 0x30;
	
	yuantai_na2(ypcode[1]);
	set_wukuaipingtai(0x03);
	
	//拿走第三个物块
	yuantai_na1(ypcode[2]); 
	
	wait_send_shumeipai(0x36,30000);
	while(1){
		if(Serial_RxPacket[0] == 0x39 && Serial_RxPacket[1] == 0x38){
			break;
		}
	}Serial_RxPacket[0] = 0x30;Serial_RxPacket[1] = 0x30;	
	
	yuantai_na2(ypcode[2]);

	TIM_SetCompare1(TIM3,0);
	//复位到识别的位置
	set_zhuashou_Angle(45.0f,200);
	move_all(-70.0f,1000,200   ,0,1000,200    ,247,13);//转过来识别
	set_wukuaipingtai(0x01);
	jixie_reset();
}

void set_maduo(void)
{
	/*====================初始化====================*/
	car_Init();
	
	/*====================启动====================*/
	car_StartToPlate();
	car_ScanQR_test();
	
	move_all(-70.0f,1000,200   ,0,1000,200    ,247,13);//转过来识别
//	PID_move(0,0,0,1000,-180.0f,4);//-180.0改为0
//	PID_move(0,0,0,1000,-180.0f,4);//-180.0改为0
//	delay_ms1(500);
//	while(1){
//		wait_send_shumeipai(0x37,10000);//如果发送了信息，但是一直没有得到回应，那么就一直发送
//		transfer_pi_position11(0x02);
//		car_move_distance(direct_x,direct_y,180,150);
//		if(Serial_RxPacket[8] != 0x34){
//			break;
//		}
//		//如果返回了没看到的信息，那就微微调整一下，再重复给地瓜派发送
//		//反之如果返回了看到的信息（也即第九位并非0x34）,则可以退出该程序
//	}

//	//角度校正
////	PID_move(0,0,0,1000,0.0f,4);//-180.0改为0
//	PID_move(0,0,0,1000,-180.0f,4);//-180.0改为0
//	delay_ms1(500);
//	
//	
//	//精细定标
//	{
//		wait_send_shumeipai(0x38,10000);//如果发送了信息，但是一直没有得到回应，那么就一直发送
//		transfer_pi_position12(0x02);	
//		if(Serial_RxPacket[8] == 0x34){
//			car_move_distance(0,0,70,50);//如果没有看到颜色，那就不移动
//		}else{	
//			car_move_distance(direct_x,direct_y,130,100);//如果看到颜色，那就按照正常的方式移动
//		}
//	}//至此第二次定标完成
//	
//	car_SeHuan1ToSeHuan2(1);
//	jixie_reset();

	
	while(1){
		wait_send_shumeipai(0x39,10000);	
		transfer_pi_position3(0x02);
		car_move_distance(direct_x,direct_y,180,150);//至此第一次定标完成
		delay_ms1(200);
		if(Serial_RxPacket[8] != 0x34){
			break;
		}
	}
	PID_move(0,0,0,1000,0.0f,4);//-180.0改为0
	
	{
		wait_send_shumeipai(0x39,10000);		
		transfer_pi_position3(0x02);	
		if(Serial_RxPacket[8] == 0x34){
			car_move_distance(0,0,70,50);
		}else{	
			car_move_distance(direct_x,direct_y,180,150);//至此第二次定标完成
		}
	}
	jixie_reset();
	set_zhuashou_Angle_kai();
	move_all(0.0f,1000,200   ,0,1000,200   ,70,13);//物块平台抓物块
	move_all(0.0f,1000,200   ,30,1000,200   ,70,13);//物块平台抓物块
	set_zhuashou_Angle_he();
	//放置第一个
	
	fangzhi_maduo(task[3]);
	
	

	set_zhuashou_Angle(45.0f,200);
	delay_ms1((int)shengjiang_control(0,2000,240));
	
	set_wukuaipingtai(0x02);
	delay_ms1((int)shengjiang_control(0,2000,240));
	move_all(0.0f,1000,200   ,30,1000,200   ,70,13);//物块平台抓物块
	set_zhuashou_Angle_he();
	
	//放置第二个	
	fangzhi_maduo(task[4]);
	
	set_wukuaipingtai(0x03);
	delay_ms1((int)shengjiang_control(0,2000,240));
	
	move_all(0.0f,1000,200   ,30,1000,200   ,70,13);//物块平台抓物块
	set_zhuashou_Angle_he();
	
	//放置第三个	
	fangzhi_maduo(task[5]);
	set_wukuaipingtai(0x01);
	jixie_reset();
	
}


void set_map(int a, int b)
{
	car_Init();
	car_Start(); //不通讯地瓜派
	map(a,b);
	map(3, 4);
	map(4, 5);
	jixie_reset();
}


