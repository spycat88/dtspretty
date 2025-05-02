test: test-mini-sample test-rg351m


test-mini-sample:
	dtc -I dts -O dtb -@ mini-sample.dts -o mini-sample.dtb
	dtc -I dtb -O dts mini-sample.dtb -o mini-sample-decompiled.dts
	../dtspretty.py -r mini-rules.yaml mini-sample-decompiled.dts > mini-sample-restored.dts
	dtc -I dts -O dtb -@ mini-sample-restored.dts -o mini-sample-rebuilt.dtb
	dtc -I dtb -O dts mini-sample-rebuilt.dtb -o mini-sample-rebuilt.dts
	cmp -s mini-sample-decompiled.dts mini-sample-rebuilt.dts

test-rg351m:
	dtc -I dts -O dtb -@ rg351m.dts -o rg351m.dtb 2>rg351m-build.err
	dtc -I dtb -O dts rg351m.dtb -o rg351m-decompiled.dts 2>/dev/null
	../dtspretty.py -r rules-rk.yaml rg351m-decompiled.dts > rg351m-restored.dts
	dtc -I dts -O dtb -@ rg351m-restored.dts -o rg351m-rebuilt.dtb 2>rg351m-rebuild.err
	dtc -I dtb -O dts rg351m-rebuilt.dtb -o rg351m-rebuilt.dts 2>/dev/null
	# due to complex structure of preprocessed rg351m.dts phandles change. Here we can only check size to ensure nothing lost
	bash -c '[[ $$(wc -c rg351m-decompiled.dts | cut -d" " -f1) == $$(wc -c rg351m-rebuilt.dts | cut -d" " -f1) ]]'
	# Also we can ensure we didn't add any new dtc build errors
	bash -c '[[ $$(wc -l rg351m-build.err | cut -d" " -f1) == $$(wc -l rg351m-rebuild.err | cut -d" " -f1) ]]'
