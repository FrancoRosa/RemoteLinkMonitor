//LinkFunctions plus interrups
#define adc_chnls 3
#define adc_smpls 50
#define rx_len 10
#define vref_addr ((uint16_t*) ((uint32_t) 0x1FFFF7BA))

const uint8_t OnCmd[] =   "@ON";
const uint8_t OffCmd[] =  "@OFF";
const uint8_t tx_per = 60;
const uint8_t rx_per = 5;

uint16_t adc_raw[adc_chnls];
uint32_t adc_pro[adc_chnls];
uint32_t adc_sum[adc_chnls];
uint8_t rx_idx, adc_idx,adc_sum_i =0;
uint8_t rx_data[2];
uint8_t rx_buffer[rx_len];
uint8_t rx_counter, tx_counter=0;

bool flagLink = true;
bool flagCommand = false;
bool flagRx,flagTx= true;

void clearbuffer()
{
  int i=0;
  for(i=0;i<rx_len;i++) rx_buffer[i]=0; 
}
void tic()
{
	HAL_GPIO_WritePin(GPIOA, LED_Pin, GPIO_PIN_SET); 
	HAL_Delay(10);	
	HAL_GPIO_WritePin(GPIOA, LED_Pin, GPIO_PIN_RESET); 
	HAL_Delay(990);
}
	
void sendData()
{
  float Vda, PVVolt, BTVolt=0;

  // LinkControl Based on linkFlag
  if(!flagLink) HAL_GPIO_WritePin(GPIOB,LK_EN_Pin,GPIO_PIN_SET);
  else HAL_GPIO_WritePin(GPIOB,LK_EN_Pin,GPIO_PIN_RESET);
  //ADC Cal: y = 10.607x + 0.5505
  Vda = 3.3*(*vref_addr)/adc_pro[2];
  BTVolt = 10.607*Vda*adc_pro[0]/4095+ 0.5505;
  PVVolt = 10.607*Vda*adc_pro[1]/4095+ 0.5505;
  printf("%2.1f, %2.1f, %d\r\n",PVVolt, BTVolt, flagLink);
  //printf("%ld, %ld, %ld, %d\r\n",adc_raw[0],adc_raw[1],adc_raw[2], flagLink);
}

void HAL_ADC_ConvCpltCallback(ADC_HandleTypeDef* hadc)
{
  if (__HAL_ADC_GET_FLAG(hadc, ADC_FLAG_EOC))
    {
    adc_raw[adc_idx] = HAL_ADC_GetValue(hadc);
    adc_idx++;
    if (adc_idx>=adc_chnls) adc_idx=0;
    }
 
  if (__HAL_ADC_GET_FLAG(hadc, ADC_FLAG_EOS))
    {
			for (adc_idx=0;adc_idx<adc_chnls;adc_idx++) 
      {adc_sum[adc_idx]=adc_sum[adc_idx]+adc_raw[adc_idx];}
			
      adc_sum_i++;
			if (adc_sum_i >= adc_smpls)
			{
				for (adc_idx=0; adc_idx<adc_chnls; adc_idx++) 
        {adc_pro[adc_idx] = adc_sum[adc_idx] / adc_smpls; adc_sum[adc_idx]=0;}
				adc_sum_i=0;
			}   
      adc_idx=0;
		}
}

void HAL_UART_RxCpltCallback(UART_HandleTypeDef *huart)
{
	uint8_t c;
	if (huart->Instance == USART1)	//current UART
		{
		HAL_GPIO_TogglePin(GPIOA,LED_Pin);
 		c=rx_data[0];
		rx_buffer[rx_idx]=c;
		rx_idx++;
		if(rx_idx>=rx_len) rx_idx=0;
		if (c == '\n')
        {
          flagCommand=true;
          rx_buffer[rx_idx]='\0';
          if(rx_idx>3)
          {
           if (memcmp(OnCmd, rx_buffer,3)==0) {flagLink=true;}
           if (memcmp(OffCmd,rx_buffer,3)==0) {flagLink=false;}
           }
        rx_idx=0;
        clearbuffer();
        }
		HAL_UART_Receive_IT(&huart1, rx_data, 1);	//activate UART receive interrupt every time
		}
 
}

void HAL_UART_TxCpltCallback(UART_HandleTypeDef *huart)
{
  if (huart->Instance == USART1)  //current UART
    {
      HAL_GPIO_TogglePin(GPIOA,LED_Pin);
    }

}

