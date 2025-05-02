DTS pretty printer
===================

This tool is created with a great help of Github Copilot.

Rationale
----------------
Sometimes we need to reverse-engineer DTB files from device vendor.  
There is a well-known tool for compilation and decompilation -- `dtc`.  
It does its job, but results are hard to compehend and compare:
```
    serial@ff030000 {
        compatible = "rockchip,px30-uart\0snps,dw-apb-uart";
        reg = <0x00 0xff030000 0x00 0x100>;
        interrupts = <0x00 0x0f 0x04>;
        clocks = <0x2e 0x06 0x2e 0x15>;
        clock-names = "baudclk\0apb_pclk";
        dmas = <0x2f 0x00 0x2f 0x01>;
        reg-shift = <0x02>;
        reg-io-width = <0x04>;
        pinctrl-names = "default";
        pinctrl-0 = <0x30 0x31 0x32>;
        status = "disabled";
        phandle = <0xe4>;
    };
```
Here we see typical issues with decompiled dts:
  * nodes are referenced by ephemeral `phandle` instead of alias
  * references to other nodes are not properly grouped
  * multiple-string options are glued with `\0`

And while we usually even have `__symbols__` table it is feasible and would be nice
to resolve `0x2f` phandles into `&references`, right?  

This tool helps with that.

Output
-------------------------
This is a real output of dtspretty when given a dts with above snippet as input:
```
    uart0: serial@ff030000 {
        compatible = "rockchip,px30-uart", "snps,dw-apb-uart";
        reg = <0x0 0xff030000 0 0x100>;
        interrupts = <0 15 4>;
        clocks = <&pmucru 6>, <&pmucru 21>;
        clock-names = "baudclk", "apb_pclk";
        dmas = <&dmac 0>, <&dmac 1>;
        reg-shift = <2>;
        reg-io-width = <4>;
        pinctrl-names = "default";
        pinctrl-0 = <&uart0_xfer &uart0_cts &uart0_rts>;
        status = "disabled";
    };
```

And this is how it looks like in [original dts](https://github.com/armbian/linux-rockchip/blob/rockchip-5.10/arch/arm64/boot/dts/rockchip/px30.dtsi#L671C1-L685C4):
```
    uart0: serial@ff030000 {
        compatible = "rockchip,px30-uart", "snps,dw-apb-uart";
        reg = <0x0 0xff030000 0x0 0x100>;
        interrupts = <GIC_SPI 15 IRQ_TYPE_LEVEL_HIGH>;
        clocks = <&pmucru SCLK_UART0_PMU>, <&pmucru PCLK_UART0_PMU>;
        clock-names = "baudclk", "apb_pclk";
        dmas = <&dmac 0>, <&dmac 1>;
        /*You can add it to enable dma*/
        /*dma-names = "tx", "rx";*/
        reg-shift = <2>;
        reg-io-width = <4>;
        pinctrl-names = "default";
        pinctrl-0 = <&uart0_xfer &uart0_cts &uart0_rts>;
        status = "disabled";
    };
```
Pretty close, huh? Constants need some more work to resolve, but they are usually easy to find and compare.

Usage
-------------------
```
$ dtspretty.py -r tmp/rules-rk.yaml tmp/k36s.dts > tmp/k36s-pretty.dts
```

You need rules (`tmp/rules-rk.yaml`) to allow the tool properly dereference input dts.  
See [complex rule file](tests/rules-rk.yaml) for a rule set used for the demo above.  
Sample rules file looks like this:
```
clock:
  patterns: ['^clocks$']
gpio:
  patterns: ['^gpios?$', '-gpios?']
pinctrl:
  patterns: ['^pinctrl-']
  struct: [ref]
rockchip,pins:
  patterns: ['^rockchip,pins$']
  struct: [d, d, d, ref]
```

These two notations are equivalent:
```
exampleprop: [ref, x, d, ref]
```
```
exampleprop:
  patterns: ['^exampleprop$']
  struct: [ref, x, d, ref]
```

If property name matches pattern, struct is applied for dereferencing phandles
If no struct is given, consider struct is dynamic:
 * first element is a ref
 * if property being parsed is named 'clock', then number of cells is indicated by '#clock-cells' property of referenced object
 * cells follow ref and are kept as numbers
 * after cells comes next ref
