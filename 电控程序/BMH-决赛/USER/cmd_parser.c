#include "cmd_parser.h"
#include "servo.h"
#include "yyb_move.h"
#include "pid.h"
#include "delay.h"
#include "Serial.h"
#include "uart6_ckp.h"
#include <string.h>
#include <stdlib.h>
#include <stdio.h>

extern float direct_x;
extern float direct_y;
extern void transfer_pi_position2(void);
extern void wait_send_shumeipai(uint8_t message, uint16_t time);
extern float move_all(float angle, int speed_x, int accel_x,
                      float grip_angle, int speed_y, int accel_y,
                      float yuntai_angle, int delay_ms);
extern float move_all1(float angle, int speed_x, int accel_x,
                       float grip_angle, int speed_y, int accel_y,
                       float yuntai_angle, int delay_ms);

char cmd_buffer[CMD_BUF_SIZE];
uint8_t cmd_ready = 0;
static uint8_t cmd_index = 0;

void CMD_Init(void)
{
	memset(cmd_buffer, 0, CMD_BUF_SIZE);
	cmd_index = 0;
	cmd_ready = 0;
}

void CMD_FeedChar(uint8_t ch)
{
	if (ch == '\r' || ch == '\n')
	{
		if (cmd_index > 0)
		{
			cmd_buffer[cmd_index] = '\0';
			cmd_ready = 1;
		}
	}
	else
	{
		if (cmd_index < CMD_BUF_SIZE - 1)
		{
			cmd_buffer[cmd_index++] = ch;
		}
	}
}

static void send_response(const char *msg)
{
	Serial_SendString((char *)msg);
	Serial_SendByte('\r');
	Serial_SendByte('\n');
}

void CMD_Process(void)
{
	char *cmd;

	cmd = strtok(cmd_buffer, " \t");
	if (cmd == NULL) goto reset;
	cmd_ready = 0;

	if (strcmp(cmd, "SERVO") == 0)
	{
		char *id_str = strtok(NULL, " \t");
		char *angle_str = strtok(NULL, " \t");
		if (id_str && angle_str)
		{
			int id = atoi(id_str);
			float angle = atof(angle_str);
			if (id == 2)
			{
				Servo_SetAngle2_zhuashou(angle);
				send_response("OK:SERVO2");
			}
			else if (id == 3)
			{
				Servo_SetAngle3_wukuaipingtai(angle);
				send_response("OK:SERVO3");
			}
			else if (id == 4)
			{
				Servo_SetAngle4_yuntai(angle);
				send_response("OK:SERVO4");
			}
			else
			{
				send_response("ERR:INVALID_SERVO_ID");
			}
		}
		else
		{
			send_response("ERR:PARAM");
		}
	}
	else if (strcmp(cmd, "LIFT") == 0)
	{
		char *dir_str = strtok(NULL, " \t");
		char *dis_str = strtok(NULL, " \t");
		char *a2_str = strtok(NULL, " \t");
		if (dir_str && dis_str && a2_str)
		{
			uint8_t dir = atoi(dir_str);
			float dis = atof(dis_str);
			uint8_t a2 = atoi(a2_str);
			shengjiang_control(dir, dis, a2);
			send_response("OK:LIFT");
		}
		else
		{
			send_response("ERR:PARAM");
		}
	}
	else if (strcmp(cmd, "PID") == 0)
	{
		char *vx_str = strtok(NULL, " \t");
		char *vy_str = strtok(NULL, " \t");
		char *w_str = strtok(NULL, " \t");
		char *time_str = strtok(NULL, " \t");
		char *target_str = strtok(NULL, " \t");
		char *choose_str = strtok(NULL, " \t");
		if (vx_str && vy_str && w_str && time_str && target_str && choose_str)
		{
			int vx = atoi(vx_str);
			int vy = atoi(vy_str);
			int w = atoi(w_str);
			uint32_t time = atoi(time_str);
			int target = atoi(target_str);
			int pid_choose = atoi(choose_str);
			PID_move(vx, vy, w, time, target, pid_choose);
			send_response("OK:PID");
		}
		else
		{
			send_response("ERR:PARAM");
		}
	}
	else if (strcmp(cmd, "CAR") == 0)
	{
		char *type_str = strtok(NULL, " \t");
		char *x_str = strtok(NULL, " \t");
		char *y_str = strtok(NULL, " \t");
		char *a_str = strtok(NULL, " \t");
		char *speed_str = strtok(NULL, " \t");
		if (type_str && x_str && y_str && a_str && speed_str)
		{
			int type = atoi(type_str);
			float x = atof(x_str);
			float y = atof(y_str);
			int a = atoi(a_str);
			int speed = atoi(speed_str);
			switch (type)
			{
				case 1: car_move1(x, y, a, speed); break;
				case 2: car_move2(x, y, a, speed); break;
				case 3: car_move3(x, y, a, speed); break;
				case 4: car_move4(x, y, a, speed); break;
				default: send_response("ERR:INVALID_CAR_TYPE"); break;
			}
			send_response("OK:CAR");
		}
		else
		{
			send_response("ERR:PARAM");
		}
	}
	else if (strcmp(cmd, "CAR_DIST") == 0)
	{
		char *x_str = strtok(NULL, " \t");
		char *y_str = strtok(NULL, " \t");
		char *a_str = strtok(NULL, " \t");
		char *speed_str = strtok(NULL, " \t");
		if (x_str && y_str && a_str && speed_str)
		{
			float x = atof(x_str);
			float y = atof(y_str);
			int a = atoi(a_str);
			int speed = atoi(speed_str);
			car_move_distance(x, y, a, speed);
			send_response("OK:CAR_DIST");
		}
		else
		{
			send_response("ERR:PARAM");
		}
	}
	else if (strcmp(cmd, "DELAY") == 0)
	{
		char *ms_str = strtok(NULL, " \t");
		if (ms_str)
		{
			uint16_t ms = atoi(ms_str);
			delay_ms1(ms);
			send_response("OK:DELAY");
		}
		else
		{
			send_response("ERR:PARAM");
		}
	}
	else if (strcmp(cmd, "ECHO") == 0)
	{
		char *msg = strtok(NULL, "");
		if (msg) send_response(msg);
		else send_response("OK:ECHO");
	}
	else if (strcmp(cmd, "PING") == 0)
	{
		send_response("PONG");
	}
	else if (strcmp(cmd, "WAIT_RPI") == 0)
	{
		char tjcstr[100];
		while (1)
		{
			if (Serial_GetRxFlag() == 1)
			{
				sprintf(tjcstr, "t0.txt=\"%d%d%d+%d%d%d \"",
					Serial_RxPacket[0]-0x30, Serial_RxPacket[1]-0x30, Serial_RxPacket[2]-0x30,
					Serial_RxPacket[4]-0x30, Serial_RxPacket[5]-0x30, Serial_RxPacket[6]-0x30);
				HMISends(tjcstr);
				HMISendb(0xff);
				break;
			}
		}
		send_response("OK:WAIT_RPI");
	}
	else if (strcmp(cmd, "RPI_CALIB") == 0)
	{
		while (1)
		{
			while (1)
			{
				if (Serial_GetRxFlag() == 1)
				{
					break;
				}
			}
			transfer_pi_position2();
			car_move_distance(direct_x, direct_y, 100, 80);
			if (Serial_RxPacket[8] != 0x34)
			{
				break;
			}
			else
			{
				wait_send_shumeipai(0x32, 15000);
			}
		}
		send_response("OK:RPI_CALIB");
	}
	else if (strcmp(cmd, "MOVE_ARM") == 0)
	{
		char *a_str = strtok(NULL, " \t");
		char *sx_str = strtok(NULL, " \t");
		char *ax_str = strtok(NULL, " \t");
		char *g_str = strtok(NULL, " \t");
		char *sy_str = strtok(NULL, " \t");
		char *ay_str = strtok(NULL, " \t");
		char *yt_str = strtok(NULL, " \t");
		char *d_str = strtok(NULL, " \t");
		if (a_str && sx_str && ax_str && g_str && sy_str && ay_str && yt_str && d_str)
		{
			float a = atof(a_str);
			int sx = atoi(sx_str);
			int ax = atoi(ax_str);
			float g = atof(g_str);
			int sy = atoi(sy_str);
			int ay = atoi(ay_str);
			float yt = atof(yt_str);
			int d = atoi(d_str);
			move_all(a, sx, ax, g, sy, ay, yt, d);
			send_response("OK:MOVE_ARM");
		}
		else
		{
			send_response("ERR:PARAM");
		}
	}
	else if (strcmp(cmd, "MOVE_ARM1") == 0)
	{
		char *a_str = strtok(NULL, " \t");
		char *sx_str = strtok(NULL, " \t");
		char *ax_str = strtok(NULL, " \t");
		char *g_str = strtok(NULL, " \t");
		char *sy_str = strtok(NULL, " \t");
		char *ay_str = strtok(NULL, " \t");
		char *yt_str = strtok(NULL, " \t");
		char *d_str = strtok(NULL, " \t");
		if (a_str && sx_str && ax_str && g_str && sy_str && ay_str && yt_str && d_str)
		{
			float a = atof(a_str);
			int sx = atoi(sx_str);
			int ax = atoi(ax_str);
			float g = atof(g_str);
			int sy = atoi(sy_str);
			int ay = atoi(ay_str);
			float yt = atof(yt_str);
			int d = atoi(d_str);
			move_all1(a, sx, ax, g, sy, ay, yt, d);
			send_response("OK:MOVE_ARM1");
		}
		else
		{
			send_response("ERR:PARAM");
		}
	}
	else if (strcmp(cmd, "STOP") == 0)
	{
		send_response("OK:STOP");
	}
	else if (strcmp(cmd, "RESET") == 0)
	{
		__disable_irq();
		NVIC_SystemReset();
	}
	else if (strcmp(cmd, "GRIPPER") == 0)
	{
		char *angle_str = strtok(NULL, " \t");
		if (angle_str)
		{
			float angle = atof(angle_str);
			Servo_SetAngle2_zhuashou(angle);
			send_response("OK:GRIPPER");
		}
		else
		{
			send_response("ERR:PARAM");
		}
	}
	else if (strcmp(cmd, "PLATFORM") == 0)
	{
		char *angle_str = strtok(NULL, " \t");
		if (angle_str)
		{
			float angle = atof(angle_str);
			Servo_SetAngle3_wukuaipingtai(angle);
			send_response("OK:PLATFORM");
		}
		else
		{
			send_response("ERR:PARAM");
		}
	}
	else if (strcmp(cmd, "YUNTAI") == 0)
	{
		char *angle_str = strtok(NULL, " \t");
		if (angle_str)
		{
			float angle = atof(angle_str);
			Servo_SetAngle4_yuntai(angle);
			send_response("OK:YUNTAI");
		}
		else
		{
			send_response("ERR:PARAM");
		}
	}
	else if (strcmp(cmd, "GROUP") == 0)
	{
		send_response("OK:GROUP_START");
	}
	else if (strcmp(cmd, "END") == 0)
	{
		send_response("OK:GROUP_END");
	}
	else
	{
		send_response("ERR:UNKNOWN_CMD");
	}

reset:
	cmd_index = 0;
	memset(cmd_buffer, 0, CMD_BUF_SIZE);
}
