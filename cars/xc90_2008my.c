//mscan 2510020
//hscan 1a2402a


static void xc90_2008my_ms_wheel_handler(const uint8_t * msg, struct msg_desc_t * desc)  // working but reversed
{
	if (is_timeout(desc)) {

		carstate.wheel = 0;
		return;
	}

	uint8_t angle = msg[6] & 0x3f;
	uint8_t wheel = scale(angle, 0, 0x3f, 0, 100);

	if (msg[5] & 0x04)
		carstate.wheel = wheel;
	else
		carstate.wheel = -wheel;
}

static void xc90_2008my_ms_gear_handler(const uint8_t * msg, struct msg_desc_t * desc)
{
	if (is_timeout(desc)) {

		carstate.selector = STATE_UNDEF;
		return;
	}

	switch ((msg[6] >> 4) & 0x07) {

		case 1:
			carstate.selector = e_selector_p;
			break;
		case 2:
			carstate.selector = e_selector_r;
			break;
		case 3:
			carstate.selector = e_selector_n;
			break;
		case 4:
			carstate.selector = e_selector_d;
			break;

		default:
			carstate.selector = e_selector_p;
			break;
	}
}

static void xc90_2008my_ms_lsm1_handler(const uint8_t * msg, struct msg_desc_t * desc)
{
	if (is_timeout(desc)) {

		carstate.illum = STATE_UNDEF;

		return;
	}
	uint8_t night_illumination_on = ((msg[2] & 0xC) > 0); // Check if the 3rd or 4th least significant bits are high
	
	carstate.illum = night_illumination_on ? 100 : 0;
}

static void xc90_2008my_ms_lsm0_handler(const uint8_t * msg, struct msg_desc_t * desc)
{
	if (is_timeout(desc)) {

		carstate.park_lights = STATE_UNDEF;
		carstate.near_lights = STATE_UNDEF;
		return;
	}

	carstate.park_lights = msg[3] & 0x04 ? 1 : 0;
	carstate.near_lights = msg[3] & 0x08 ? 1 : 0;
}

static void xc90_2008my_ms_rem_handler(const uint8_t * msg, struct msg_desc_t * desc)
{
	if (is_timeout(desc)) {

		carstate.fl_door = STATE_UNDEF;
		carstate.fr_door = STATE_UNDEF;
		carstate.rl_door = STATE_UNDEF;
		carstate.rr_door = STATE_UNDEF;
		carstate.bonnet = STATE_UNDEF;
		carstate.tailgate = STATE_UNDEF;

		carstate.radar.state = e_radar_off;
		return;
	}

	carstate.fl_door = (msg[5] & 0x02) ? 1 : 0;
	carstate.fr_door = (msg[5] & 0x04) ? 1 : 0;
	carstate.rl_door = (msg[5] & 0x08) ? 1 : 0;
	carstate.rr_door = (msg[5] & 0x10) ? 1 : 0;
	carstate.bonnet = (msg[5] & 0x41) ? 1 : 0;
	carstate.tailgate = (msg[5] & 0x20) ? 1 : 0;

	uint8_t v = (msg[3] >> 3) & 0x1f;
	v = scale(v, 0x00, 0x1f, 0, 99);

	//uint8_t who = msg[3] & 0x7;

	uint8_t on = (msg[2] & 0x01) ? 0x1 : 0x0;
	if (e_selector_r != car_get_selector())
		on = 0x0;

	carstate.radar.state = on ? e_radar_on : e_radar_off;
	carstate.radar.rl = v;
	carstate.radar.rlm = v;
	carstate.radar.rrm = v;
	carstate.radar.rr = v;
	//No front radar on my MY2008
	carstate.radar.fl = 0;
	carstate.radar.flm = 0;
	carstate.radar.frm = 0;
	carstate.radar.fr = 0;
}

static void xc90_2008my_ms_swm_handler(const uint8_t * msg, struct msg_desc_t * desc)
{
	if (is_timeout(desc)) {
		key_state.key_volume = STATE_UNDEF;
		key_state.key_mode = STATE_UNDEF;
		key_state.key_prev = STATE_UNDEF;
		key_state.key_next = STATE_UNDEF;
		key_state.key_pickup = STATE_UNDEF;
		key_state.key_hangup = STATE_UNDEF;
		key_state.key_nav_enter = STATE_UNDEF;
		key_state.key_nav_back = STATE_UNDEF;
		key_state.key_nav_up = STATE_UNDEF;
		key_state.key_nav_down = STATE_UNDEF;
		key_state.key_nav_left = STATE_UNDEF;
		key_state.key_nav_right = STATE_UNDEF;
	
		return;
	}

	//up
	if (!(msg[7] & 0x08)) {

		if ((key_state.key_volume != 1) && key_state.key_cb && key_state.key_cb->inc_volume)
			key_state.key_cb->inc_volume(1);

		key_state.key_volume = 1;
	}
	//down
	else if (!(msg[7] & 0x04)) {

		if ((key_state.key_volume != 0) && key_state.key_cb && key_state.key_cb->dec_volume)
			key_state.key_cb->dec_volume(1);

		key_state.key_volume = 0;
	}
	else
		key_state.key_volume = STATE_UNDEF;

	//PREV
	uint8_t key_prev = msg[7] & 0x01;
	//1->0 short release
	if ((key_state.key_prev == 1) && (key_prev == 0) && key_state.key_cb && key_state.key_cb->prev)
		key_state.key_cb->prev();
	key_state.key_prev = key_prev;

	//NEXT
	uint8_t key_next = (msg[7] >> 1) & 0x01;
	//1->0 short release
	if ((key_state.key_next == 1) && (key_next == 0) && key_state.key_cb && key_state.key_cb->next)
		key_state.key_cb->next();
	key_state.key_next = key_next;

	//PICKUP
	uint8_t key_pickup = (msg[7] >> 5) & 0x01; //Pickup and hangup swapped from 2007
	//1->0 short release
	if ((key_state.key_pickup== 1) && (key_pickup == 0) && key_state.key_cb && key_state.key_cb->pickup)
		key_state.key_cb->pickup();
	
	key_state.key_pickup = key_pickup;

	//HANGUP 
	uint8_t key_hangup = (msg[7] >> 4) & 0x01; //Pickup and hangup swapped from 2007
	//1->0 short release
	if ((key_state.key_hangup == 1) && (key_hangup == 0) && key_state.key_cb && key_state.key_cb->hangup)
		key_state.key_cb->hangup();
	key_state.key_hangup = key_hangup;




	// RTI GPS Nav

	//NAV_ENTER
	uint8_t key_nav_enter = (msg[6] >> 5) & 0x01;
	//1->0 short release
	if ((key_state.key_nav_enter == 0) && (key_nav_enter == 1) && key_state.key_cb && key_state.key_cb->nav_enter)
		key_state.key_cb->nav_enter();
	key_state.key_nav_enter = key_nav_enter;

	//NAV_BACK
	uint8_t key_nav_back = (msg[6] >> 4)& 0x01;
	//1->0 short release
	if ((key_state.key_nav_back == 0) && (key_nav_back == 1) && key_state.key_cb && key_state.key_cb->nav_back)
		key_state.key_cb->nav_back();
	key_state.key_nav_back = key_nav_back;

	//NAV_UP
	uint8_t key_nav_up = (msg[6] >> 3)& 0x01;
	//1->0 short release
	if ((key_state.key_nav_up == 0) && (key_nav_up == 1) && key_state.key_cb && key_state.key_cb->nav_up)
		key_state.key_cb->nav_up();
	key_state.key_nav_up = key_nav_up;

	//NAV_DOWN
	uint8_t key_nav_down = (msg[6] >> 2)& 0x01;
	//1->0 short release
	if ((key_state.key_nav_down == 0) && (key_nav_down == 1) && key_state.key_cb && key_state.key_cb->nav_down)
		key_state.key_cb->nav_down();
	key_state.key_nav_down = key_nav_down;
	
	//NAV_LEFT
	uint8_t key_nav_left = (msg[6] >> 1) & 0x01;
	//1->0 short release
	if ((key_state.key_nav_left == 0) && (key_nav_left == 1) && key_state.key_cb && key_state.key_cb->nav_left)
		key_state.key_cb->nav_left();
	key_state.key_nav_left = key_nav_left;

	//NAV_RIGHT
	uint8_t key_nav_right = msg[6] & 0x01; //Left and right swapped from 2007MY
	//1->0 short release
	if ((key_state.key_nav_right == 0) && (key_nav_right == 1) && key_state.key_cb && key_state.key_cb->nav_right)
		key_state.key_cb->nav_right();
	key_state.key_nav_right = key_nav_right;

}

static void xc90_2008my_ms_acc_handler(const uint8_t * msg, struct msg_desc_t * desc)
{
	if (is_timeout(desc)) {

		carstate.acc = STATE_UNDEF;
		carstate.ign = STATE_UNDEF;

		return;
	}

	if (msg[1] & 0x40)
		carstate.acc = 1;
	else
		carstate.acc = 0;

	if (msg[1] & 0x20)
		carstate.ign = 1;
	else
		carstate.ign = 0;
}

static void xc90_2008my_ms_ccm_handler(const uint8_t * msg, struct msg_desc_t * desc){
	if (is_timeout(desc)) {
		carstate.temp = STATE_UNDEF;
		car_air_state.fanspeed = STATE_UNDEF;
		car_air_state.recycling = STATE_UNDEF;
		car_air_state.powerfull = STATE_UNDEF;
		car_air_state.ac = STATE_UNDEF;
		return;
	}
	uint8_t fanspeed= ((msg[7] & 0xf0) >> 4);

	carstate.temp = (msg[6] * 0.75 - 48)+0.5f; // cabin temperature
	car_air_state.fanspeed = (fanspeed > 0x07? 0x7 : fanspeed) * 2 + 2;
	car_air_state.powerfull = fanspeed > 0x07 ? 1 : 0;
	car_air_state.recycling = (msg[1] == 0x64) ? 1 : 0;
	car_air_state.ac = msg[1] != 0x00 && msg[1] != 0x64 ? 1 : 0;
}



static void xc90_2008my_ms_odo_handler(const uint8_t * msg, struct msg_desc_t * desc){
	if (is_timeout(desc)) {
		carstate.odometer = STATE_UNDEF;
		return;
	}

	uint32_t odometer = 0;
	odometer |= (uint32_t)msg[5] << 16; // Shift the 6th byte 16 bits to the left
    odometer |= (uint32_t)msg[6] << 8;  // Shift the 7th byte 8 bits to the left
    odometer |= (uint32_t)msg[7];       // Add the 8th byte
    carstate.odometer = odometer;
}

static void xc90_2008my_ms_rpm_handler(const uint8_t * msg, struct msg_desc_t * desc){
	if (is_timeout(desc)) {
		carstate.taho = STATE_UNDEF;
		return;
	}
	uint16_t rpm = 0;
    rpm |= (uint16_t)msg[6] << 8;  // Shift the 6th byte 8 bits to the left
    rpm |= (uint16_t)msg[7];
    rpm = rpm & 0x0FFF; //Only lowest 12 bits seems to encode rpm
    carstate.taho = rpm; 
}

static void xc90_2008my_ms_vel_handler(const uint8_t * msg, struct msg_desc_t * desc){
	if (is_timeout(desc)) {
		carstate.speed = STATE_UNDEF;
		return;
	}

	uint16_t speed = 0;
    speed |= (uint16_t)msg[5] << 8;  // Shift the 6th byte 8 bits to the left
    speed |= (uint16_t)msg[6]; // Add the 7th byte
    speed = speed & 0x03FF; //only the lowest 10 bits are used to denote speed 
    speed = speed / 4; //Express in km/h
    carstate.speed = speed; 
}

static void xc90_2008my_ms_fuel_handler(const uint8_t * msg, struct msg_desc_t * desc){
	if (is_timeout(desc)) {
		carstate.fuel_lvl = STATE_UNDEF;
		return;
	}

	const uint8_t tank_capacity = 80; //80 Litres on the V8
	uint8_t fuel_lvl = tank_capacity * msg[6] / 100; //6th byte encodes percentage full (most likely)
    carstate.fuel_lvl = fuel_lvl; 
}

static void xc90_2008my_ms_temp_handler(const uint8_t * msg, struct msg_desc_t * desc){
	if (is_timeout(desc)) {
		carstate.temp = STATE_UNDEF;
		return;
	}
	//I have not managed to correctly scale this.
	uint32_t temp = 0;
	//temp = (msg[6] * 0.75 - 48)+0.5f;
    temp = msg[6];
    //2C outside gives 0 on HU
    carstate.temp = temp; 
}

static void xc90_2008my_ms_ds_belt_handler(const uint8_t * msg, struct msg_desc_t * desc){
    carstate.ds_belt = (msg[4] & 0x08) >> 3;  
}

static void xc90_2008my_ms_park_brake_handler(const uint8_t * msg, struct msg_desc_t * desc){
    carstate.park_break = ~msg[1] & 0x01;  
}

struct msg_desc_t xc90_2008my_ms[] =
{
	{ 0x0217ffc, 20, 0, 0, xc90_2008my_ms_lsm0_handler },
	{ 0x131726c, 25, 0, 0, xc90_2008my_ms_swm_handler },
	{ 0x12173be, 45, 0, 0, xc90_2008my_ms_rem_handler },
	{ 0x2510020, 80, 0, 0, xc90_2008my_ms_wheel_handler },
	{ 0x2803008, 60, 0, 0, xc90_2008my_ms_lsm1_handler }, 
	{ 0x3200428, 90, 0, 0, xc90_2008my_ms_gear_handler },
	{ 0x2006428, 120, 0, 0, xc90_2008my_ms_acc_handler },
	{ 0x4000002, 1000, 0, 0, xc90_2008my_ms_odo_handler }, //Confirmed working
	{ 0x2803008, 180, 0, 0, xc90_2008my_ms_rpm_handler }, //Confirmed working
	{ 0x217FFC, 150, 0, 0, xc90_2008my_ms_vel_handler }, //Confirmed working
	{ 0x381526C, 240, 0, 0, xc90_2008my_ms_fuel_handler }, //Likely correct
	{ 0x2202262, 270, 0, 0, xc90_2008my_ms_ds_belt_handler }, //Confirmed working
	{ 0x3A04004, 300, 0, 0, xc90_2008my_ms_park_brake_handler }, //Confirmed working
	{ 0x3C01428, 1000, 0, 0, xc90_2008my_ms_temp_handler }, //TODO: confirm CAN scaling + uart
	//{ 0xE01008, 300, 0, 0, xc90_2008my_ms_ccm_handler }, //TODO: confirm CAN scaling + uart
};

/*Todos (Reverse engineering CAN ids and message bytes):

* Battery voltage
* Wiper fluid level
* Exterior temp
* CCM integration

*/
