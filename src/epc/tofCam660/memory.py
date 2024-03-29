

class Memory(object):
    """Use factory method 'create(revision)' to instantiate"""

    @staticmethod
    def create(revision):
        catalog = {0: MemoryRev0}
        return catalog[revision]()

    def getAddress(self, registername):
        return self.registers[registername].address

    def __iter__(self):
        return self.registers.keys().__iter__()


class Register:
    def __init__(self, address):
        self.address = address


class MemoryRev0(Memory):
    def __init__(self):
        self.registers = {'ic_type': Register(0x00),
                          'ic_version': Register(0x01),
                          'mem_ctrl_conf_0': Register(0x02),
                          'mem_ctrl_conf_1': Register(0x03),
                          'ee_page': Register(0x10),
                          'ee_addr': Register(0x11),
                          'ee_data': Register(0x12),
                          'ee_mask': Register(0x13),
                          'prog_ee_req': Register(0x14),
                          'prot_conf_en_0': Register(0x15),
                          'prot_conf_en_1': Register(0x16),
                          'ee_read_trim': Register(0x17),
                          'ee_read_time': Register(0x18),
                          'ee_write_time': Register(0x19),
                          'ee_bist_test_loop': Register(0x1a),
                          'ee_test': Register(0x1b),
                          'strap_hi': Register(0x20),
                          'strap_lo': Register(0x21),
                          'mt_0_hi': Register(0x22),
                          'mt_0_mi': Register(0x23),
                          'mt_0_lo': Register(0x24),
                          'mt_1_hi': Register(0x25),
                          'mt_1_mi': Register(0x26),
                          'mt_1_lo': Register(0x27),
                          'mt_2_hi': Register(0x28),
                          'mt_2_mi': Register(0x29),
                          'mt_2_lo': Register(0x2a),
                          'mt_3_hi': Register(0x2b),
                          'mt_3_mi': Register(0x2c),
                          'mt_3_lo': Register(0x2d),
                          'mt_4_hi': Register(0x2e),
                          'mt_4_mi': Register(0x2f),
                          'mt_4_lo': Register(0x30),
                          'mt_5_hi': Register(0x31),
                          'mt_5_mi': Register(0x32),
                          'mt_5_lo': Register(0x33),
                          'mt_6_hi': Register(0x34),
                          'mt_6_mi': Register(0x35),
                          'mt_6_lo': Register(0x36),
                          'mt_7_hi': Register(0x37),
                          'mt_7_mi': Register(0x38),
                          'mt_7_lo': Register(0x39),
                          'mt_8_hi': Register(0x3a),
                          'mt_8_mi': Register(0x3b),
                          'mt_8_lo': Register(0x3c),
                          'mt_9_hi': Register(0x3d),
                          'mt_9_mi': Register(0x3e),
                          'mt_9_lo': Register(0x3f),
                          'sr_address': Register(0x40),
                          'sr_data_0': Register(0x41),
                          'sr_data_1': Register(0x42),
                          'sr_data_2': Register(0x43),
                          'sr_data_3': Register(0x44),
                          'sr_data_4': Register(0x45),
                          'sr_data_5': Register(0x46),
                          'sr_program': Register(0x47),
                          'tcmi_sir1_hi': Register(0x48),
                          'tcmi_sir1_lo': Register(0x49),
                          'tcmi_sir2_hi': Register(0x4a),
                          'tcmi_sir2_lo': Register(0x4b),
                          'tcmi_sir3_hi': Register(0x4c),
                          'tcmi_sir3_lo': Register(0x4d),
                          'tcmi_bypass': Register(0x4e),
                          'adc_refgen_enable': Register(0x4f),
                          'readout_max_range_hi': Register(0x50),
                          'readout_max_range_lo': Register(0x51),
                          'readout_min_range_hi': Register(0x52),
                          'readout_min_range_lo': Register(0x53),
                          'top_range_failures_over_hi': Register(0x54),
                          'top_range_failures_over_lo': Register(0x55),
                          'top_range_failures_under_hi': Register(0x56),
                          'top_range_failures_unter_lo': Register(0x57),
                          'bot_range_failures_over_hi': Register(0x58),
                          'bot_range_failures_over_lo': Register(0x59),
                          'bot_range_failures_under_hi': Register(0x5a),
                          'bot_range_failures_unter_lo': Register(0x5b),
                          'range_test_modes': Register(0x5c),
                          'range_results_status': Register(0x5d),
                          'vref_t_enable': Register(0x5e),
                          'vref_b_enable': Register(0x5f),
                          'sum_temp_tl_hi': Register(0x60),
                          'sum_temp_tl_lo': Register(0x61),
                          'sum_temp_tr_hi': Register(0x62),
                          'sum_temp_tr_lo': Register(0x63),
                          'sum_temp_bl_hi': Register(0x64),
                          'sum_temp_bl_lo': Register(0x65),
                          'sum_temp_br_hi': Register(0x66),
                          'sum_temp_br_lo': Register(0x67),
                          'max_temp_range_hi': Register(0x68),
                          'max_temp_range_lo': Register(0x69),
                          'min_temp_range_hi': Register(0x6a),
                          'min_temp_range_lo': Register(0x6b),
                          'temp_range_check': Register(0x6c),
                          'temp_range_errors': Register(0x6d),
                          'testaio1_mux_ctrl': Register(0x6e),
                          'testaio2_mux_ctrl': Register(0x6f),
                          'dll_status': Register(0x70),
                          'dll_fine_ctrl_ext_hi': Register(0x71),
                          'dll_fine_ctrl_ext_lo': Register(0x72),
                          'dll_coarse_ctrl_ext': Register(0x73),
                          'dll_fine_bank_rb_hi': Register(0x74),
                          'dll_fine_bank_rb_lo': Register(0x75),
                          'dll_fine_low_bank_rb_hi': Register(0x76),
                          'dll_fine_low_bank_rb_lo': Register(0x77),
                          'dll_fine_page_rb': Register(0x78),
                          'dll_coarse_rb': Register(0x79),
                          'dll_test_mode': Register(0x7a),
                          'pixel_test': Register(0x7b),
                          'analog_test': Register(0x7c),
                          'cfg_mode_control': Register(0x7d),
                          'cfg_mode_status': Register(0x7e),
                          'page': Register(0x7f),
                          'clk_enables': Register(0x80),
                          'pll_pre_post_dividers': Register(0x81),
                          'pll_fb_divider': Register(0x82),
                          'sys_clk_divider': Register(0x83),
                          'dll_clk_divider': Register(0x84),
                          'mod_clk_divider': Register(0x85),
                          'seq_clk_divider': Register(0x86),
                          'refgen_clk_divider': Register(0x87),
                          'isource_clk_divider': Register(0x88),
                          'tcmi_clk_divider': Register(0x89),
                          'ee_cp_clk_divider': Register(0x8a),
                          'demodulation_delays': Register(0x8b),
                          'pn_poly_hi': Register(0x8c),
                          'pn_poly_lo': Register(0x8d),
                          'pn_init_hi': Register(0x8e),
                          'pn_init_lo': Register(0x8f),
                          'led_driver': Register(0x90),
                          'seq_control': Register(0x91),
                          'mod_control': Register(0x92),
                          'dist_offset': Register(0x93),
                          'resolution_reduction': Register(0x94),
                          'readout_dir': Register(0x95),
                          'roi_tl_x_hi': Register(0x96),
                          'roi_tl_x_lo': Register(0x97),
                          'roi_br_x_hi': Register(0x98),
                          'roi_br_x_lo': Register(0x99),
                          'roi_tl_y': Register(0x9a),
                          'roi_br_y': Register(0x9b),
                          'sir_hi': Register(0x9c),
                          'sir_lo': Register(0x9d),
                          'int_len_mgx1_hi': Register(0x9e),
                          'int_len_mgx2_lo': Register(0x9f),
                          'intm_hi': Register(0xa0),
                          'intm_lo': Register(0xa1),
                          'int_len_hi': Register(0xa2),
                          'int_len_lo': Register(0xa3),
                          'shutter_control': Register(0xa4),
                          'power_control': Register(0xa5),
                          'dll_en_del_hi': Register(0xa6),
                          'dll_en_del_lo': Register(0xa7),
                          'dll_en_hi': Register(0xa8),
                          'dll_en_lo': Register(0xa9),
                          'dll_measurement_rate_hi': Register(0xaa),
                          'dll_measurement_rate_lo': Register(0xab),
                          'dll_filter': Register(0xac),
                          'dll_match_width': Register(0xad),
                          'dll_control': Register(0xae),
                          'sat_threshold': Register(0xaf),
                          'flim_t1_hi': Register(0xb0),
                          'flim_t1_lo': Register(0xb1),
                          'flim_t2_hi': Register(0xb2),
                          'flim_t2_lo': Register(0xb3),
                          'flim_t3_hi': Register(0xb4),
                          'flim_t3_lo': Register(0xb5),
                          'flim_t4_hi': Register(0xb6),
                          'flim_t4_lo': Register(0xb7),
                          'flim_trep_hi': Register(0xb8),
                          'flim_trep_lo': Register(0xb9),
                          'flim_repetitions_hi': Register(0xba),
                          'flim_repetitions_lo': Register(0xbb),
                          'flim_flash_delay_hi': Register(0xbc),
                          'flim_flash_delay_lo': Register(0xbd),
                          'flim_flash_width_hi': Register(0xbe),
                          'flim_flash_width_lo': Register(0xbf),
                          'fs_t1_hi': Register(0xc0),
                          'fs_t1_lo': Register(0xc1),
                          'fs_t2_hi': Register(0xc2),
                          'fs_t2_lo': Register(0xc3),
                          'fs_t3_hi': Register(0xc4),
                          'fs_t3_lo': Register(0xc5),
                          'fs_t4_hi': Register(0xc6),
                          'fs_t4_lo': Register(0xc7),
                          'fs_t5_hi': Register(0xc8),
                          'fs_t5_lo': Register(0xc9),
                          'i2c_address': Register(0xca),
                          'i2c_tcmi_control': Register(0xcb),
                          'tcmi_polarity': Register(0xcc),
                          'adc_ramp': Register(0xcd),
                          'iref_trim': Register(0xce),
                          'bgap_trim': Register(0xcf),
                          'vref_t_trim1': Register(0xd0),
                          'vref_t_trim2': Register(0xd1),
                          'vref_t_trim3': Register(0xd2),
                          'vref_t_trim4': Register(0xd3),
                          'vref_t_trim5': Register(0xd4),
                          'vref_t_trim6': Register(0xd5),
                          'vref_t_trim7': Register(0xd6),
                          'vref_b_trim1': Register(0xd7),
                          'vref_b_trim2': Register(0xd8),
                          'vref_b_trim3': Register(0xd9),
                          'vref_b_trim4': Register(0xda),
                          'vref_b_trim5': Register(0xdb),
                          'vref_b_trim6': Register(0xdc),
                          'vref_b_trim7': Register(0xdd),
                          'pixel_field_trim': Register(0xde),
                          'dll_filter_control': Register(0xdf),
                          'adc_refgen_tl_trim1': Register(0xe0),
                          'adc_refgen_tl_trim2': Register(0xe1),
                          'adc_refgen_tr_trim1': Register(0xe2),
                          'adc_refgen_tr_trim2': Register(0xe3),
                          'adc_refgen_bl_trim1': Register(0xe4),
                          'adc_refgen_bl_trim2': Register(0xe5),
                          'adc_refgen_br_trim1': Register(0xe6),
                          'adc_refgen_br_trim2': Register(0xe7),
                          'temp_tl_cal1': Register(0xe8),
                          'temp_tl_cal2': Register(0xe9),
                          'temp_tr_cal1': Register(0xea),
                          'temp_tr_cal2': Register(0xeb),
                          'temp_bl_cal1': Register(0xec),
                          'temp_bl_cal2': Register(0xed),
                          'temp_br_cal1': Register(0xee),
                          'temp_br_cal2': Register(0xef),
                          'user_1': Register(0xf0),
                          'user_2': Register(0xf1),
                          'ee_ramp_div_msb': Register(0xf2),
                          'ee_ramp_div_lsb': Register(0xf3),
                          'ee_pre_div': Register(0xf4),
                          'customer_id': Register(0xf5),
                          'wafer_id_msb': Register(0xf6),
                          'wafer_id_lsb': Register(0xf7),
                          'chip_id_msb': Register(0xf8),
                          'chip_id_lsb': Register(0xf9),
                          'part_type': Register(0xfa),
                          'part_version': Register(0xfb),
                          'reg_wr_protection': Register(0xfc),
                          'reg_rd_protection': Register(0xfd),
                          'ee_wr_protection': Register(0xfe),
                          'ee_rd_protection': Register(0xff), }
