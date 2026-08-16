#include "stm32f4xx.h"                  // Device header
#include "yyb_move.h"
#include "math.h"
#include "servo.h"
#include "delay.h"

typedef struct {
    float start_angle;    	//��ʲô�Ƕȿ�ʼ
    float target_angle;	  	//Ŀ������ת���ٽǶ�
    float current_angle;  	//��ǰ�ĽǶ��Ƕ���
    int moving_flag;    // ��ֵ���±�־��1: �����˶���0: ����
    float t;            // ʱ����������ڲ�ֵ����?
	float time;		  //������ֵ�˶������ʱ��?
    void (*SetServoAngle)(float angle);  // ���õ�ǰ�Ƕȵĺ���ָ��
} Servo_t;

Servo_t yuantai = {77.4f, 0.0f, 77.4f, 0, 0, 0, Servo_SetAngle4_yuntai};
Servo_t zhuashou = {2.7f, 2.7f, 2.7f, 0, 0, 0, Servo_SetAngle2_zhuashou};
Servo_t wukuaipingtai = {20.0f, 20.0f, 20.0f, 0, 0, 0,Servo_SetAngle3_wukuaipingtai};

void PWM_Init(void)
{
	/* ����ʱ�� */
	RCC_APB1PeriphClockCmd(RCC_APB1Periph_TIM2, ENABLE);			// ����TIM2��ʱ��
	RCC_AHB1PeriphClockCmd(RCC_AHB1Periph_GPIOA, ENABLE);			// ����GPIOA��ʱ��
	
	/* GPIO��ʼ�� */
	GPIO_InitTypeDef GPIO_InitStructure;
	GPIO_InitStructure.GPIO_Mode = GPIO_Mode_AF;					// ����ģʽ
	GPIO_InitStructure.GPIO_Pin = GPIO_Pin_1 | GPIO_Pin_2 | GPIO_Pin_3; // ����PA1, PA2, PA3
	GPIO_InitStructure.GPIO_Speed = GPIO_Speed_50MHz;
	GPIO_InitStructure.GPIO_OType = GPIO_OType_PP;					// �������?
	GPIO_InitStructure.GPIO_PuPd = GPIO_PuPd_NOPULL;				// ��ʹ������������
	GPIO_Init(GPIOA, &GPIO_InitStructure);							// ��ʼ��GPIOA
	
	// ����GPIO���ù���ΪTIM2
	GPIO_PinAFConfig(GPIOA, GPIO_PinSource1, GPIO_AF_TIM2);  // PA1 -> TIM2_CH2
	GPIO_PinAFConfig(GPIOA, GPIO_PinSource2, GPIO_AF_TIM2);  // PA2 -> TIM2_CH3
	GPIO_PinAFConfig(GPIOA, GPIO_PinSource3, GPIO_AF_TIM2);  // PA3 -> TIM2_CH4

	/* ����ʱ��Դ */
	TIM_InternalClockConfig(TIM2);		// ѡ��TIM2Ϊ�ڲ�ʱ��
	
	/* ʱ����Ԫ��ʼ�� */
	TIM_TimeBaseInitTypeDef TIM_TimeBaseInitStructure;				
	TIM_TimeBaseInitStructure.TIM_ClockDivision = TIM_CKD_DIV1;     // ʱ�ӷ�Ƶ��ѡ�񲻷�Ƶ
	TIM_TimeBaseInitStructure.TIM_CounterMode = TIM_CounterMode_Up; // ������ģʽ��ѡ�����ϼ���
	TIM_TimeBaseInitStructure.TIM_Period = 20000 - 1;				// �������ڣ���ARR��ֵ������PWM����
	TIM_TimeBaseInitStructure.TIM_Prescaler = 84 - 1;				// Ԥ��Ƶ��������PWMƵ��
	TIM_TimeBaseInitStructure.TIM_RepetitionCounter = 0;            // �ظ�������
	TIM_TimeBaseInit(TIM2, &TIM_TimeBaseInitStructure);             // ��ʼ��TIM2ʱ����Ԫ
	
	/* ����Ƚϳ�ʼ��?*/ 
	TIM_OCInitTypeDef TIM_OCInitStructure;							
	TIM_OCStructInit(&TIM_OCInitStructure);                         
	
	// ����ͨ��
	TIM_OCInitStructure.TIM_OCMode = TIM_OCMode_PWM1;               // ����Ƚ�ģʽ��ѡ��PWMģʽ1
	TIM_OCInitStructure.TIM_OCPolarity = TIM_OCPolarity_High;       // ������ԣ�ѡ��Ϊ��?
	TIM_OCInitStructure.TIM_OutputState = TIM_OutputState_Enable;   // ���ʹ��?
	TIM_OCInitStructure.TIM_Pulse = 0;							    // ����ռ�ձ�
	TIM_OC2Init(TIM2, &TIM_OCInitStructure);                        // ��ʼ��TIM2������Ƚ�ͨ��?
	TIM_OC3Init(TIM2, &TIM_OCInitStructure);                        // ��ʼ��TIM2������Ƚ�ͨ��?
	TIM_OC4Init(TIM2, &TIM_OCInitStructure);                        // ��ʼ��TIM2������Ƚ�ͨ��?
    
	NVIC_InitTypeDef NVIC_InitStructure;
    // ����NVIC
    NVIC_InitStructure.NVIC_IRQChannel = TIM2_IRQn;
    NVIC_InitStructure.NVIC_IRQChannelPreemptionPriority = 1;
    NVIC_InitStructure.NVIC_IRQChannelSubPriority = 1;
    NVIC_InitStructure.NVIC_IRQChannelCmd = ENABLE;
    NVIC_Init(&NVIC_InitStructure);
	
	/* TIMʹ�� */
	TIM_Cmd(TIM2, ENABLE);			// ʹ��TIM2����ʱ����ʼ����
	TIM_SetCompare2(TIM2, 520);		// ץ��
	TIM_SetCompare3(TIM2, 648);		// ���ƽ�?
	TIM_SetCompare4(TIM2, 930);		// ��̨
	TIM_ITConfig(TIM2, TIM_IT_Update, ENABLE);
}

void PWM_SetCompare2(uint16_t Compare)
{
	TIM_SetCompare2(TIM2, Compare);		// ����CCR2��ֵ
}

void PWM_SetCompare3(uint16_t Compare)
{
	TIM_SetCompare3(TIM2, Compare);		// ����CCR3��ֵ
}

void PWM_SetCompare4(uint16_t Compare)
{
	TIM_SetCompare4(TIM2, Compare);		// ����CCR4��ֵ
}

// ��������������Ŀ��Ƕȣ���Ա仯����********
void set_servo_angle(Servo_t *servo, float target)
{
    servo->target_angle = target;
    servo->moving_flag = 1;
}

// ��ֵ����
float interpolate(float start, float target, float t) {
    if (t < 200) {
        return (25.0f / 8.0f) * target * pow(t / 1000.0f, 2) + start;
    } else if (t < 800) {
        return (5.0f / 4.0f) * target * (t / 1000.0f) - target / 8.0f + start;
    } else if (t < 1000) {
        return (-25.0f / 8.0f) * target * pow(t / 1000.0f, 2) + (25.0f / 4.0f) * target * (t / 1000.0f) - (17.0f / 8.0f) * target + start;
    } else {
        return start + target;
    }
}

// ��ֵ���º���
void servo_update(Servo_t *servo) {
	double tau,s;
    if (servo->moving_flag == 1) {
		servo->t +=20;
		tau = servo->t / servo->time;
			if (tau <= 0.0) {
				servo->current_angle = servo->start_angle;
			} else if (tau >= 1.0) {
				servo->current_angle = servo->target_angle;
				servo->start_angle = servo->target_angle;
				servo->t = 0;
				servo->moving_flag = 0;
			} else {
				s = 6 * tau * tau * tau * tau * tau
				  - 15 * tau * tau * tau * tau
				  + 10 * tau * tau * tau;
				servo->current_angle = servo->start_angle + (servo->target_angle - servo->start_angle) * s;
			}	
        servo->SetServoAngle(servo->current_angle);
    }
}


//278��Ϊץ����λ��
//???��Ϊ���õ����ƽ̨��λ��?
//64.8��Ϊ��ʼλ��
void set_yuantai_Angle(float target, float time){
    Servo_t *servo = &yuantai;
	if(target<=45.8f){
		target = 45.8f;
	}
    servo->target_angle = target;
	servo->time = time;
    servo->moving_flag = 1;
    // �ȴ��˶���ɣ�ע�������Ϊ�ȴ�moving_flagΪ0
//    while(servo->moving_flag != 0){}
//    delay_ms1(50);
}

//2.7��Ϊ��ʼλ��
//10��Ϊץ����λ��
//60���ſ���צ
void set_zhuashou_Angle(float target, float time){
	target -=1.0f; 
    Servo_t *servo = &zhuashou;
    servo->target_angle = target;
	servo->time = time;
    servo->moving_flag = 1;
    // �ȴ��˶���ɣ�ע�������Ϊ�ȴ�moving_flagΪ0
    while(servo->moving_flag != 0){}
    delay_ms1(30);
}

void set_zhuashou_Angle_kai(void)
{
	set_zhuashou_Angle(25.0f, 300);
}

void set_zhuashou_Angle_he(void)
{
	set_zhuashou_Angle(1.0f, 300);
}

//20.0f�ȷ�������?
//20.0f+113.0f�ȷ�������
//20.0f+113.0f+117.0f�ȷ��������?
void set_wukuaipingtai_Angle(float target, float time){
    Servo_t *servo = &wukuaipingtai;
    servo->target_angle = target;
	servo->time = time;
    servo->moving_flag = 1;
//    // �ȴ��˶���ɣ�ע�������Ϊ�ȴ�moving_flagΪ0
    while(servo->moving_flag != 0){}
    delay_ms1(50);
}

void set_wukuaipingtai(uint8_t task){
    if(task == 0x01){
		set_wukuaipingtai_Angle(20.0f,300);
	}else if(task == 0x02){
		set_wukuaipingtai_Angle(20.0f+124.0f,300);
	}else if(task == 0x03){
		set_wukuaipingtai_Angle(20.0f+123.0f+115.0f,300);
	}
}

//不阻塞版�?只发送目�?不等待完�?可与其他运动并行
void set_wukuaipingtai_Angle_nb(float target, float time){
    Servo_t *servo = &wukuaipingtai;
    servo->target_angle = target;
	servo->time = time;
    servo->moving_flag = 1;
}

void set_zhuashou_Angle_nb(float target, float time){
	target -=1.0f; 
    Servo_t *servo = &zhuashou;
    servo->target_angle = target;
	servo->time = time;
    servo->moving_flag = 1;
}

//等待舵机运动完成
void servo_wait_done(Servo_t *servo){
    while(servo->moving_flag != 0){}
}

// ͳһ���������ŷ��ĸ��º���
void TIM2_IRQHandler(void) {
    if (TIM_GetITStatus(TIM2, TIM_IT_Update) != RESET) {
        // �ֱ���������ŷ��Ĳ��?
        servo_update(&yuantai);
        servo_update(&zhuashou);
        servo_update(&wukuaipingtai);

        TIM_ClearITPendingBit(TIM2, TIM_IT_Update);
    }
}

/*ǰ���������ֱ�Ϊ
	ƽ�Ƶ�Ŀ��λ�ã�65.0f �� -122.0 ֮��
	ƽ�Ƶ��ٶȣ� 1000 rpm
	ƽ�Ƶļ��ٶȣ�200rpm
  �м����������ֱ�Ϊ
	������Ŀ��λ�ã�0.0f �� 130.0f
	�������ٶȣ�1000 rpm
	�����ļ��ٶȣ�200 rpm
  ������������ֱ��?
	��̨��Ŀ��λ�ã�0 �� 360
	��̨��ת�٣�13����

*/
int move_all(float target_pos, uint16_t speed, uint8_t accel,float target_pos1, uint16_t speed1, uint16_t accel1,float target, float speed_of_yuntai)
{	
//	accel1 = 200;
//	accel = 200;
//	speed1 = 2000;
	target = target + 9.2f;
	double time1 = pingtui_control(target_pos,speed,accel);
	double time2 = shengjiang_control(target_pos1,speed1,accel1);
//	double time = 100 * fabs(target - yuantai.current_angle)/speed_of_yuntai;
	double time;
	if(fabs(target - yuantai.current_angle) <= 28){
		time = 120 * fabs(target - yuantai.current_angle)/13.0f;
	}else if(fabs(target - yuantai.current_angle) <= 50){
		time = 100 * fabs(target - yuantai.current_angle)/13.0f;
	}else if(fabs(target - yuantai.current_angle) <= 100){
		time = 85 * fabs(target - yuantai.current_angle)/13.0f;
	}else if(fabs(target - yuantai.current_angle) <= 150){
		time = 70 * fabs(target - yuantai.current_angle)/13.0f;
	}else if(fabs(target - yuantai.current_angle) <= 250){
		time = 60 * fabs(target - yuantai.current_angle)/13.0f;
	}else{
		time = 50 * fabs(target - yuantai.current_angle)/13.0f;
	}
//	time = time * (2-0.1*speed_of_yuntai);
	set_yuantai_Angle(target,time);
	double max = fmax(time, fmax(time1, time2));
	delay_ms1((int)max);
	return (int)max;
}


int move_all1(float target_pos, uint16_t speed, uint8_t accel,float target_pos1, uint16_t speed1, uint8_t accel1,float target, float speed_of_yuntai)
{	
	accel1 = 240;
	accel = 230;
	speed1 = 2000;
	target = target + 9.2f;
	double time1 = pingtui_control(target_pos,speed,accel);
	double time2 = shengjiang_control(target_pos1,speed1,accel1);
//	double time = 100 * fabs(target - yuantai.current_angle)/speed_of_yuntai;
	double time;
	if(fabs(target - yuantai.current_angle) <= 28){
		time = 120 * fabs(target - yuantai.current_angle)/13.0f;
	}else if(fabs(target - yuantai.current_angle) <= 50){
		time = 100 * fabs(target - yuantai.current_angle)/13.0f;
	}else if(fabs(target - yuantai.current_angle) <= 100){
		time = 85 * fabs(target - yuantai.current_angle)/13.0f;
	}else if(fabs(target - yuantai.current_angle) <= 150){
		time = 70 * fabs(target - yuantai.current_angle)/13.0f;
	}else if(fabs(target - yuantai.current_angle) <= 250){
		time = 60 * fabs(target - yuantai.current_angle)/13.0f;
	}else{
		time = 50 * fabs(target - yuantai.current_angle)/13.0f;
	}
	set_yuantai_Angle(target,time);
	double max = fmax(time, fmax(time1, time2));
	return (int)max;
}

