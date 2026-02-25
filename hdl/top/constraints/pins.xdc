## pins.xdc -- Pin constraints for Digilent Arty A7-35T
## Modify for your target board.

## Clock (100 MHz oscillator)
set_property -dict { PACKAGE_PIN E3  IOSTANDARD LVCMOS33 } [get_ports {clk}]
create_clock -period 10.000 -name sys_clk [get_ports {clk}]

## Reset (active-low, BTN0)
set_property -dict { PACKAGE_PIN D9  IOSTANDARD LVCMOS33 } [get_ports {rst_n}]

## LEDs
set_property -dict { PACKAGE_PIN H5  IOSTANDARD LVCMOS33 } [get_ports {led[0]}]
set_property -dict { PACKAGE_PIN J5  IOSTANDARD LVCMOS33 } [get_ports {led[1]}]
set_property -dict { PACKAGE_PIN T9  IOSTANDARD LVCMOS33 } [get_ports {led[2]}]
set_property -dict { PACKAGE_PIN T10 IOSTANDARD LVCMOS33 } [get_ports {led[3]}]

## Configuration voltages (suppresses Vivado DRC warnings)
set_property CFGBVS VCCO [current_design]
set_property CONFIG_VOLTAGE 3.3 [current_design]
