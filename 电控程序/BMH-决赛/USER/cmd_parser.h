#ifndef __CMD_PARSER_H
#define __CMD_PARSER_H

#include <stdio.h>

#define CMD_BUF_SIZE 128

extern char cmd_buffer[];
extern uint8_t cmd_ready;

void CMD_Init(void);
void CMD_FeedChar(uint8_t ch);
void CMD_Process(void);

#endif
