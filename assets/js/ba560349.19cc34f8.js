"use strict";(self.webpackChunkdocusaurus=self.webpackChunkdocusaurus||[]).push([[252],{3905:(t,e,a)=>{a.d(e,{Zo:()=>s,kt:()=>m});var n=a(7294);function i(t,e,a){return e in t?Object.defineProperty(t,e,{value:a,enumerable:!0,configurable:!0,writable:!0}):t[e]=a,t}function l(t,e){var a=Object.keys(t);if(Object.getOwnPropertySymbols){var n=Object.getOwnPropertySymbols(t);e&&(n=n.filter((function(e){return Object.getOwnPropertyDescriptor(t,e).enumerable}))),a.push.apply(a,n)}return a}function r(t){for(var e=1;e<arguments.length;e++){var a=null!=arguments[e]?arguments[e]:{};e%2?l(Object(a),!0).forEach((function(e){i(t,e,a[e])})):Object.getOwnPropertyDescriptors?Object.defineProperties(t,Object.getOwnPropertyDescriptors(a)):l(Object(a)).forEach((function(e){Object.defineProperty(t,e,Object.getOwnPropertyDescriptor(a,e))}))}return t}function o(t,e){if(null==t)return{};var a,n,i=function(t,e){if(null==t)return{};var a,n,i={},l=Object.keys(t);for(n=0;n<l.length;n++)a=l[n],e.indexOf(a)>=0||(i[a]=t[a]);return i}(t,e);if(Object.getOwnPropertySymbols){var l=Object.getOwnPropertySymbols(t);for(n=0;n<l.length;n++)a=l[n],e.indexOf(a)>=0||Object.prototype.propertyIsEnumerable.call(t,a)&&(i[a]=t[a])}return i}var u=n.createContext({}),p=function(t){var e=n.useContext(u),a=e;return t&&(a="function"==typeof t?t(e):r(r({},e),t)),a},s=function(t){var e=p(t.components);return n.createElement(u.Provider,{value:e},t.children)},h={inlineCode:"code",wrapper:function(t){var e=t.children;return n.createElement(n.Fragment,{},e)}},N=n.forwardRef((function(t,e){var a=t.components,i=t.mdxType,l=t.originalType,u=t.parentName,s=o(t,["components","mdxType","originalType","parentName"]),N=p(a),m=i,d=N["".concat(u,".").concat(m)]||N[m]||h[m]||l;return a?n.createElement(d,r(r({ref:e},s),{},{components:a})):n.createElement(d,r({ref:e},s))}));function m(t,e){var a=arguments,i=e&&e.mdxType;if("string"==typeof t||i){var l=a.length,r=new Array(l);r[0]=N;var o={};for(var u in e)hasOwnProperty.call(e,u)&&(o[u]=e[u]);o.originalType=t,o.mdxType="string"==typeof t?t:i,r[1]=o;for(var p=2;p<l;p++)r[p]=a[p];return n.createElement.apply(null,r)}return n.createElement.apply(null,a)}N.displayName="MDXCreateElement"},8418:(t,e,a)=>{a.r(e),a.d(e,{assets:()=>u,contentTitle:()=>r,default:()=>h,frontMatter:()=>l,metadata:()=>o,toc:()=>p});var n=a(7462),i=(a(7294),a(3905));const l={},r="Link Adaptation Tests",o={unversionedId:"tests/Link_Adaptation",id:"tests/Link_Adaptation",title:"Link Adaptation Tests",description:"All Tests",source:"@site/../docs/tests/Link_Adaptation.md",sourceDirName:"tests",slug:"/tests/Link_Adaptation",permalink:"/terragraph-ctf/tests/Link_Adaptation",draft:!1,editUrl:"https://github.com/terragraph/terragraph-ctf/edit/main/docs/../docs/tests/Link_Adaptation.md",tags:[],version:"current",frontMatter:{},sidebar:"docs",previous:{title:"Throughput Tests",permalink:"/terragraph-ctf/tests/Throughput"},next:{title:"Interference Tests",permalink:"/terragraph-ctf/tests/Interference"}},u={},p=[{value:"All Tests",id:"all-tests",level:2},{value:"<code>PUMA_RF_LA-0.1</code> UDP Throughput with Fixed MCS VS Link Adaptation",id:"puma_rf_la-01-udp-throughput-with-fixed-mcs-vs-link-adaptation",level:3},{value:"<code>PUMA_RF_LA-0.2</code> TCP stability with Fixed MCS VS Link Adaptation",id:"puma_rf_la-02-tcp-stability-with-fixed-mcs-vs-link-adaptation",level:3},{value:"<code>PUMA_RF_LA-1.0</code> Point-to-MultiPoint Link Stability with Link Adaptation",id:"puma_rf_la-10-point-to-multipoint-link-stability-with-link-adaptation",level:3},{value:"<code>PUMA_RF_LA-2.1</code> Gradually increase/decrease attenuation on a link (ramp test)",id:"puma_rf_la-21-gradually-increasedecrease-attenuation-on-a-link-ramp-test",level:3},{value:"Post-Processing Data",id:"post-processing-data",level:4},{value:"<code>PUMA_RF_LA-2.2</code> Gradually Increase and Decrease Attenuation on a Point to MultiPoint Setup (Simultaneous Ramp Test)",id:"puma_rf_la-22-gradually-increase-and-decrease-attenuation-on-a-point-to-multipoint-setup-simultaneous-ramp-test",level:3},{value:"<code>PUMA_RF_LA-3.1</code> Point-to-Point Link Survivability with High Attenuation and Traffic",id:"puma_rf_la-31-point-to-point-link-survivability-with-high-attenuation-and-traffic",level:3},{value:"<code>PUMA_RF_LA-3.2</code> Point-to-Multi-Point Link Survivability with High Attenuation and traffic",id:"puma_rf_la-32-point-to-multi-point-link-survivability-with-high-attenuation-and-traffic",level:3},{value:"<code>PUMA_RF_LA-3.3</code> Stability of Link Adaptation to small scale fades",id:"puma_rf_la-33-stability-of-link-adaptation-to-small-scale-fades",level:3},{value:"<code>PUMA_RF_LA-4.0</code> Stability of Link Adaptation across the range of SNRs",id:"puma_rf_la-40-stability-of-link-adaptation-across-the-range-of-snrs",level:3},{value:"<code>PUMA_RF_LA-4.1</code> Point-to-Point Link RAMP TEST for TPC",id:"puma_rf_la-41-point-to-point-link-ramp-test-for-tpc",level:3},{value:"<code>PUMA_RF_LA-4.2</code> Point-to-Point Link high attenuation TEST for TPC",id:"puma_rf_la-42-point-to-point-link-high-attenuation-test-for-tpc",level:3}],s={toc:p};function h(t){let{components:e,...a}=t;return(0,i.kt)("wrapper",(0,n.Z)({},s,a,{components:e,mdxType:"MDXLayout"}),(0,i.kt)("h1",{id:"link-adaptation-tests"},"Link Adaptation Tests"),(0,i.kt)("h2",{id:"all-tests"},"All Tests"),(0,i.kt)("h3",{id:"puma_rf_la-01-udp-throughput-with-fixed-mcs-vs-link-adaptation"},(0,i.kt)("inlineCode",{parentName:"h3"},"PUMA_RF_LA-0.1")," UDP Throughput with Fixed MCS VS Link Adaptation"),(0,i.kt)("p",null,"Description: The purpose of this test to ensure that LA's performance is at\nleast as good as Fixed MCS, given the link SNR yields < 0.1% PER for that MCS."),(0,i.kt)("p",null,"Test Setup: P2P setup"),(0,i.kt)("p",null,"Procedure:"),(0,i.kt)("ul",null,(0,i.kt)("li",{parentName:"ul"},"Program front/back attenuators with no attenuation."),(0,i.kt)("li",{parentName:"ul"},"Reboot the TGs, the DN and the CN."),(0,i.kt)("li",{parentName:"ul"},"For each MCSx in the set {9, 10, 11, 12}, repeat the following tests:"),(0,i.kt)("li",{parentName:"ul"},"On both the DN and CN, update ",(0,i.kt)("inlineCode",{parentName:"li"},"/etc/e2e_config/fw_cfg.json")," to reflect the\nfollowing:",(0,i.kt)("ul",{parentName:"li"},(0,i.kt)("li",{parentName:"ul"},"Fix the MCS to MCSx."),(0,i.kt)("li",{parentName:"ul"},"Disable TPC."))),(0,i.kt)("li",{parentName:"ul"},"Associate both DN and CN."),(0,i.kt)("li",{parentName:"ul"},"Program the attenuator to ensure that STF SNR is at least 2dB above the min\nSNR for MCSx (LA-TB-1 only)."),(0,i.kt)("li",{parentName:"ul"},"Ping DN \u2192 CN and CN \u2192 DN to validate connectivity."),(0,i.kt)("li",{parentName:"ul"},"Run iPerf (on the TG) for 10 mins with the following parameters:",(0,i.kt)("ul",{parentName:"li"},(0,i.kt)("li",{parentName:"ul"},"Push rate TBD"),(0,i.kt)("li",{parentName:"ul"},"Packet size of 1500 bytes."))),(0,i.kt)("li",{parentName:"ul"},"Record the throughput on the link in each direction."),(0,i.kt)("li",{parentName:"ul"},"On both the DN and CN, update ",(0,i.kt)("inlineCode",{parentName:"li"},"/etc/e2e_config/fw_cfg.json")," to reflect the\nfollowing:",(0,i.kt)("ul",{parentName:"li"},(0,i.kt)("li",{parentName:"ul"},"Enable link adaptation on the link with Max MCS = MCSx picked in the\nearlier step."),(0,i.kt)("li",{parentName:"ul"},"Disable TPC."))),(0,i.kt)("li",{parentName:"ul"},"Associate both DN and CN."),(0,i.kt)("li",{parentName:"ul"},"Ping DN \u2192 CN and CN \u2192 DN to validate connectivity."),(0,i.kt)("li",{parentName:"ul"},"Run iPerf (on the TG) for 10 mins with the following parameters:",(0,i.kt)("ul",{parentName:"li"},(0,i.kt)("li",{parentName:"ul"},"Push rate TBD"),(0,i.kt)("li",{parentName:"ul"},"Packet size of 1500 bytes"))),(0,i.kt)("li",{parentName:"ul"},"Record the throughput on the link in each direction.")),(0,i.kt)("p",null,"Pass Criterion:"),(0,i.kt)("ul",null,(0,i.kt)("li",{parentName:"ul"},"The mean UDP throughput with Link Adaptation is within 95% of Fixed MCS\nperformance."),(0,i.kt)("li",{parentName:"ul"},"Long term PER < Target PER throughout the run."),(0,i.kt)("li",{parentName:"ul"},"Short term PER < 1%+Target PER throughout the run.")),(0,i.kt)("h3",{id:"puma_rf_la-02-tcp-stability-with-fixed-mcs-vs-link-adaptation"},(0,i.kt)("inlineCode",{parentName:"h3"},"PUMA_RF_LA-0.2")," TCP stability with Fixed MCS VS Link Adaptation"),(0,i.kt)("p",null,"Description: The purpose of this test is to ensure that LA maintains good and\nstable TCP performance as compared to Fixed MCS."),(0,i.kt)("p",null,"Test Setup: P2P setup"),(0,i.kt)("p",null,"Procedure:"),(0,i.kt)("ul",null,(0,i.kt)("li",{parentName:"ul"},"Program front/back attenuators with no attenuation."),(0,i.kt)("li",{parentName:"ul"},"Reboot the TGs, the DN and the CN."),(0,i.kt)("li",{parentName:"ul"},"For each MCSx in the set {9, 10, 11, 12}, repeat the following tests:"),(0,i.kt)("li",{parentName:"ul"},"On both the DN and CN, update ",(0,i.kt)("inlineCode",{parentName:"li"},"/etc/e2e_config/fw_cfg.json")," to reflect the\nfollowing:",(0,i.kt)("ul",{parentName:"li"},(0,i.kt)("li",{parentName:"ul"},"Fix the MCS to MCSx."),(0,i.kt)("li",{parentName:"ul"},"Disable TPC."))),(0,i.kt)("li",{parentName:"ul"},"Associate both DN and CN."),(0,i.kt)("li",{parentName:"ul"},"Program the attenuator to ensure that STF SNR is at least 2dB above the min\nSNR for MCSx (LA-TB-1 only)."),(0,i.kt)("li",{parentName:"ul"},"Ping DN \u2192 CN and CN \u2192 DN to validate connectivity."),(0,i.kt)("li",{parentName:"ul"},"Run iPerf (on the TG) for 10 mins with the following parameters:",(0,i.kt)("ul",{parentName:"li"},(0,i.kt)("li",{parentName:"ul"},"Push rate TBD"),(0,i.kt)("li",{parentName:"ul"},"Packet size of 1500 bytes"))),(0,i.kt)("li",{parentName:"ul"},"Record the throughput on the link in each direction."),(0,i.kt)("li",{parentName:"ul"},"On both the DN and CN, update ",(0,i.kt)("inlineCode",{parentName:"li"},"/etc/e2e_config/fw_cfg.json")," to reflect the\nfollowing:",(0,i.kt)("ul",{parentName:"li"},(0,i.kt)("li",{parentName:"ul"},"Enable link adaptation on the link with Max MCS = MCSx picked in the\nearlier step."))),(0,i.kt)("li",{parentName:"ul"},"Associate both DN and CN."),(0,i.kt)("li",{parentName:"ul"},"Ping DN \u2192 CN and CN \u2192 DN to validate connectivity."),(0,i.kt)("li",{parentName:"ul"},"Run iPerf (on the TG) for 10 mins with the following parameters:",(0,i.kt)("ul",{parentName:"li"},(0,i.kt)("li",{parentName:"ul"},"Push rate TBD"),(0,i.kt)("li",{parentName:"ul"},"Packet size of 1500 bytes"))),(0,i.kt)("li",{parentName:"ul"},"Record the throughput on the link in each direction.")),(0,i.kt)("p",null,"Pass/Fail Criterion:"),(0,i.kt)("ul",null,(0,i.kt)("li",{parentName:"ul"},"The mean TCP throughput with Link Adaptation is within 95% of Fixed MCS\nperformance."),(0,i.kt)("li",{parentName:"ul"},"Long term PER < Target PER throughout the run."),(0,i.kt)("li",{parentName:"ul"},"Short term PER < 1%+Target PER throughout the run.")),(0,i.kt)("h3",{id:"puma_rf_la-10-point-to-multipoint-link-stability-with-link-adaptation"},(0,i.kt)("inlineCode",{parentName:"h3"},"PUMA_RF_LA-1.0")," Point-to-MultiPoint Link Stability with Link Adaptation"),(0,i.kt)("p",null,"Description: The purpose of this test is to ensure that LA maintains good TCP\nperformance for both links on a P2MP setup."),(0,i.kt)("p",null,"Test Setup: P2MP-2 setup"),(0,i.kt)("p",null,"Procedure:"),(0,i.kt)("ul",null,(0,i.kt)("li",{parentName:"ul"},"Program front/back attenuators with no attenuation."),(0,i.kt)("li",{parentName:"ul"},"Reboot the TGs, the DN, CN1 and CN2."),(0,i.kt)("li",{parentName:"ul"},"For each MCSx in the set {9, 10, 12}, repeat the following tests:"),(0,i.kt)("li",{parentName:"ul"},"On both the DN, CN1, and CN2, update ",(0,i.kt)("inlineCode",{parentName:"li"},"/etc/e2e_config/fw_cfg.json")," to reflect\nthe following:",(0,i.kt)("ul",{parentName:"li"},(0,i.kt)("li",{parentName:"ul"},"Fix the MCS to MCSx."),(0,i.kt)("li",{parentName:"ul"},"Disable TPC and set txPowerIndex on both sides to 31 for MCS 9, 27 for MCS\n10 and 25 for MCS12"))),(0,i.kt)("li",{parentName:"ul"},"Associate both DN and CN1."),(0,i.kt)("li",{parentName:"ul"},"Ping DN \u2192 CN1 and CN1 \u2192 DN to validate connectivity."),(0,i.kt)("li",{parentName:"ul"},"Associate both DN and CN2."),(0,i.kt)("li",{parentName:"ul"},"Ping DN \u2192 CN2 and CN2 \u2192 DN to validate connectivity."),(0,i.kt)("li",{parentName:"ul"},"Run iPerf (on the TG) for 10 mins on both links with the following parameters:",(0,i.kt)("ul",{parentName:"li"},(0,i.kt)("li",{parentName:"ul"},"Push rate limited to 1.25 Gbps (-b 1250m)"),(0,i.kt)("li",{parentName:"ul"},"MTU size of 1500 bytes (since it is TCP iPerf will pick the corresponding\npacket size0"))),(0,i.kt)("li",{parentName:"ul"},"Record the throughput on the link in each direction."),(0,i.kt)("li",{parentName:"ul"},"On both the DN, CN1, and CN2, Enable link adaptation on the link with Max MCS\n= MCSx picked in the earlier step."),(0,i.kt)("li",{parentName:"ul"},"Re-associate both DN and CN1.",(0,i.kt)("ul",{parentName:"li"},(0,i.kt)("li",{parentName:"ul"},"Re-associate both DN and CN2."))),(0,i.kt)("li",{parentName:"ul"},"Ping DN \u2192 CN1 and CN1 \u2192 DN to validate connectivity."),(0,i.kt)("li",{parentName:"ul"},"Ping DN \u2192 CN2 and CN2 \u2192 DN to validate connectivity."),(0,i.kt)("li",{parentName:"ul"},"Run iPerf (on the TG) for 10 mins on both links with the following parameters:",(0,i.kt)("ul",{parentName:"li"},(0,i.kt)("li",{parentName:"ul"},"Push rate limited to 1.25 Gbps (-b 1250m)"),(0,i.kt)("li",{parentName:"ul"},"MTU size of 1500 bytes (since it is TCP iPerf will pick the corresponding\npacket size0"))),(0,i.kt)("li",{parentName:"ul"},"Record the throughput on the link in each direction.")),(0,i.kt)("p",null,"Pass/Fail Criteria:"),(0,i.kt)("ul",null,(0,i.kt)("li",{parentName:"ul"},"TCP throughput is stable over both the DN-CN1 and CN-CN2 links, with a\nstandard deviation of < 30 Mbps."),(0,i.kt)("li",{parentName:"ul"},"The mean TCP throughput with Link Adaptation is within 95% of Fixed MCS\nperformance for both the links."),(0,i.kt)("li",{parentName:"ul"},"Long term PER < Target PER throughout the run."),(0,i.kt)("li",{parentName:"ul"},"Short term PER < 1%+Target PER throughout the run.")),(0,i.kt)("h3",{id:"puma_rf_la-21-gradually-increasedecrease-attenuation-on-a-link-ramp-test"},(0,i.kt)("inlineCode",{parentName:"h3"},"PUMA_RF_LA-2.1")," Gradually increase/decrease attenuation on a link (ramp test)"),(0,i.kt)("p",null,"Description: The purpose of this test is to insure that LA adaptation picks the\nright MCS as the SNR is varied across the link using a programmable attenuator\nwhile running iPerf over the wireless link."),(0,i.kt)("p",null,"Test Setup: P2P setup"),(0,i.kt)("p",null,"Procedure:"),(0,i.kt)("ul",null,(0,i.kt)("li",{parentName:"ul"},"Program attenuator with 0 dB attenuation."),(0,i.kt)("li",{parentName:"ul"},"Reboot both TGs, the DN and the CN."),(0,i.kt)("li",{parentName:"ul"},"On both the DN and CN1, update ",(0,i.kt)("inlineCode",{parentName:"li"},"/etc/e2e_config/fw_cfg.json")," to reflect the\nfollowing:",(0,i.kt)("ul",{parentName:"li"},(0,i.kt)("li",{parentName:"ul"},"Disable TPC."))),(0,i.kt)("li",{parentName:"ul"},"Init and Config FW on DN and CN."),(0,i.kt)("li",{parentName:"ul"},"Associate both DN and CN."),(0,i.kt)("li",{parentName:"ul"},"Ping DN \u2192 CN and CN \u2192 DN to validate connectivity."),(0,i.kt)("li",{parentName:"ul"},"Measure STF SNR on the link and compute median link SNR."),(0,i.kt)("li",{parentName:"ul"},"Program attenuation limit for the test (i.e. AttenMax) to ensure STF SNR is\nno less than 5 dB."),(0,i.kt)("li",{parentName:"ul"},"Run iPerf (on the TG) in the background with the following parameters:",(0,i.kt)("ul",{parentName:"li"},(0,i.kt)("li",{parentName:"ul"},"Push rate TBD"),(0,i.kt)("li",{parentName:"ul"},"Packet size of 1500 bytes"))),(0,i.kt)("li",{parentName:"ul"},"Every 40 seconds, increase the attenuation by 1dB until you reach AttenMax"),(0,i.kt)("li",{parentName:"ul"},"Every 40 seconds, decrease the attenuation by 1dB until attenuation reaches 0."),(0,i.kt)("li",{parentName:"ul"},"Terminate iPerf after going through all attenuations")),(0,i.kt)("p",null,"Pass/Fail Criterion:"),(0,i.kt)("ul",null,(0,i.kt)("li",{parentName:"ul"},"For ",(0,i.kt)("em",{parentName:"li"},"MCS_i"),", validate that > 90% of the SNR values between ","[threshold_i,\nthreshold_j]"," have ",(0,i.kt)("em",{parentName:"li"},"MCS_i")," as the PHY data rate for the link."),(0,i.kt)("li",{parentName:"ul"},"Effective throughput > 90% of expected rate throughout the test."),(0,i.kt)("li",{parentName:"ul"},"Long term PER < Target PER throughout the run."),(0,i.kt)("li",{parentName:"ul"},"Short term PER < 1%+Target PER throughout the run.")),(0,i.kt)("h4",{id:"post-processing-data"},"Post-Processing Data"),(0,i.kt)("ul",null,(0,i.kt)("li",{parentName:"ul"},"Collect STF SNR values for the CN link."),(0,i.kt)("li",{parentName:"ul"},"Create histogram of SNRs within ranges of ",(0,i.kt)("em",{parentName:"li"},"threshold_i"),"  to ",(0,i.kt)("em",{parentName:"li"},"threshold_j"),",\nwhere ",(0,i.kt)("em",{parentName:"li"},"threshold_i")," is the threshold for ",(0,i.kt)("em",{parentName:"li"},"MCS_i")," and ",(0,i.kt)("em",{parentName:"li"},"threshold_j")," is the\nthreshold for the next highest ",(0,i.kt)("em",{parentName:"li"},"MCS_j"),". For example, for MCS 9, ",(0,i.kt)("em",{parentName:"li"},"threshold_i"),"\n= 9 and ",(0,i.kt)("em",{parentName:"li"},"threshold_j")," = 11.5 (as seen in Table 1 below). The thresholds are\ndefined depending on whether the test is undergoing increase or decrease in\nattenuation.")),(0,i.kt)("p",null,(0,i.kt)("strong",{parentName:"p"},"Table 1:")),(0,i.kt)("table",null,(0,i.kt)("thead",{parentName:"table"},(0,i.kt)("tr",{parentName:"thead"},(0,i.kt)("th",{parentName:"tr",align:null},"Min Expected SNR (dB) for Ramp Down (Attenuation Increase)"),(0,i.kt)("th",{parentName:"tr",align:null},"Max Expected SNR (dB) for Ramp up (Attenuation Decrease)"),(0,i.kt)("th",{parentName:"tr",align:null},"Selected MCS"),(0,i.kt)("th",{parentName:"tr",align:null},"Effective Data Rate (Mbps)"))),(0,i.kt)("tbody",{parentName:"table"},(0,i.kt)("tr",{parentName:"tbody"},(0,i.kt)("td",{parentName:"tr",align:null},"17"),(0,i.kt)("td",{parentName:"tr",align:null},"18"),(0,i.kt)("td",{parentName:"tr",align:null},"12"),(0,i.kt)("td",{parentName:"tr",align:null},"1939")),(0,i.kt)("tr",{parentName:"tbody"},(0,i.kt)("td",{parentName:"tr",align:null},"15"),(0,i.kt)("td",{parentName:"tr",align:null},"16"),(0,i.kt)("td",{parentName:"tr",align:null},"11"),(0,i.kt)("td",{parentName:"tr",align:null},"1616")),(0,i.kt)("tr",{parentName:"tbody"},(0,i.kt)("td",{parentName:"tr",align:null},"13"),(0,i.kt)("td",{parentName:"tr",align:null},"14"),(0,i.kt)("td",{parentName:"tr",align:null},"10"),(0,i.kt)("td",{parentName:"tr",align:null},"1292")),(0,i.kt)("tr",{parentName:"tbody"},(0,i.kt)("td",{parentName:"tr",align:null},"11.5"),(0,i.kt)("td",{parentName:"tr",align:null},"12.5"),(0,i.kt)("td",{parentName:"tr",align:null},"9"),(0,i.kt)("td",{parentName:"tr",align:null},"1050")),(0,i.kt)("tr",{parentName:"tbody"},(0,i.kt)("td",{parentName:"tr",align:null},"9"),(0,i.kt)("td",{parentName:"tr",align:null},"10"),(0,i.kt)("td",{parentName:"tr",align:null},"8"),(0,i.kt)("td",{parentName:"tr",align:null},"969")),(0,i.kt)("tr",{parentName:"tbody"},(0,i.kt)("td",{parentName:"tr",align:null},"7.5"),(0,i.kt)("td",{parentName:"tr",align:null},"8.5"),(0,i.kt)("td",{parentName:"tr",align:null},"7"),(0,i.kt)("td",{parentName:"tr",align:null},"808")),(0,i.kt)("tr",{parentName:"tbody"},(0,i.kt)("td",{parentName:"tr",align:null},"5.5"),(0,i.kt)("td",{parentName:"tr",align:null},"6.5"),(0,i.kt)("td",{parentName:"tr",align:null},"6"),(0,i.kt)("td",{parentName:"tr",align:null},"646")),(0,i.kt)("tr",{parentName:"tbody"},(0,i.kt)("td",{parentName:"tr",align:null},"5"),(0,i.kt)("td",{parentName:"tr",align:null},"6"),(0,i.kt)("td",{parentName:"tr",align:null},"5"),(0,i.kt)("td",{parentName:"tr",align:null},"525")),(0,i.kt)("tr",{parentName:"tbody"},(0,i.kt)("td",{parentName:"tr",align:null},"4.5"),(0,i.kt)("td",{parentName:"tr",align:null},"5.5"),(0,i.kt)("td",{parentName:"tr",align:null},"4"),(0,i.kt)("td",{parentName:"tr",align:null},"485")),(0,i.kt)("tr",{parentName:"tbody"},(0,i.kt)("td",{parentName:"tr",align:null},"3"),(0,i.kt)("td",{parentName:"tr",align:null},"4"),(0,i.kt)("td",{parentName:"tr",align:null},"3"),(0,i.kt)("td",{parentName:"tr",align:null},"404")),(0,i.kt)("tr",{parentName:"tbody"},(0,i.kt)("td",{parentName:"tr",align:null},"2.5"),(0,i.kt)("td",{parentName:"tr",align:null},"3.5"),(0,i.kt)("td",{parentName:"tr",align:null},"2"),(0,i.kt)("td",{parentName:"tr",align:null},"323")),(0,i.kt)("tr",{parentName:"tbody"},(0,i.kt)("td",{parentName:"tr",align:null},"1"),(0,i.kt)("td",{parentName:"tr",align:null},"2"),(0,i.kt)("td",{parentName:"tr",align:null},"1"),(0,i.kt)("td",{parentName:"tr",align:null},"162")))),(0,i.kt)("h3",{id:"puma_rf_la-22-gradually-increase-and-decrease-attenuation-on-a-point-to-multipoint-setup-simultaneous-ramp-test"},(0,i.kt)("inlineCode",{parentName:"h3"},"PUMA_RF_LA-2.2")," Gradually Increase and Decrease Attenuation on a Point to MultiPoint Setup (Simultaneous Ramp Test)"),(0,i.kt)("p",null,"Description: The purpose of this test is to ensure that Link Adaptation\ncorrectly adapts the MCS on each link for a P2MP setup. Furthermore, LA is able\nto ensure that the aggregate throughput on both links is approximately constant."),(0,i.kt)("p",null,"Test Setup: P2MP-2 setup"),(0,i.kt)("p",null,"Procedure:"),(0,i.kt)("ul",null,(0,i.kt)("li",{parentName:"ul"},"Program attenuator with 0 dB attenuation."),(0,i.kt)("li",{parentName:"ul"},"Reboot both TGs, the DN and the CN."),(0,i.kt)("li",{parentName:"ul"},"On both the DN, CN1, and CN2, update ",(0,i.kt)("inlineCode",{parentName:"li"},"/etc/e2e_config/fw_cfg.json")," to reflect\nthe following:",(0,i.kt)("ul",{parentName:"li"},(0,i.kt)("li",{parentName:"ul"},"Disable TPC."))),(0,i.kt)("li",{parentName:"ul"},"Init and Config FW on DN and CN."),(0,i.kt)("li",{parentName:"ul"},"Associate both DN and CN1 and DN and CN2."),(0,i.kt)("li",{parentName:"ul"},"Ping DN \u2192 CN1 and CN1 \u2192 DN to validate connectivity."),(0,i.kt)("li",{parentName:"ul"},"Ping DN \u2192 CN2 and CN2 \u2192 DN to validate connectivity."),(0,i.kt)("li",{parentName:"ul"},"Measure STF SNR on the link and compute median link SNR."),(0,i.kt)("li",{parentName:"ul"},"Program attenuation limit for DN-CN1 (i.e. AttenMax) to ensure STF SNR is no\nless than 5 dB."),(0,i.kt)("li",{parentName:"ul"},"Program attenuation for DN-CN2 such that the STF SNR is ~5dB on the link."),(0,i.kt)("li",{parentName:"ul"},"Run iPerf (on the TG) in the background with the following parameters:",(0,i.kt)("ul",{parentName:"li"},(0,i.kt)("li",{parentName:"ul"},"2 Gbps of UDP traffic (bi-directional)"),(0,i.kt)("li",{parentName:"ul"},"Packet size of 1500 bytes"))),(0,i.kt)("li",{parentName:"ul"},"Every 40 seconds, increase the attenuation by 1dB on DN-CN1 and decrease\nattenuation by 1 dB on DN-CN2. Continue until AttenMax is reached on DN-CN1\nand 0 is reached on DN-CN2."),(0,i.kt)("li",{parentName:"ul"},"Every 40 seconds, decrease the attenuation by 1dB on DN-CN1 and increase\nattenuation by 1 dB on DN-CN2. Continue until AttenMax is reached on DN-CN2\nand 0 is reached on DN-CN1."),(0,i.kt)("li",{parentName:"ul"},"Terminate iPerf after going through all attenuations")),(0,i.kt)("p",null,"Pass/Fail Criterion:"),(0,i.kt)("ul",null,(0,i.kt)("li",{parentName:"ul"},"The MCS is correctly chosen, as a function of SNR,  based on the criterion\ndiscussed in LA-2.0."),(0,i.kt)("li",{parentName:"ul"},"Long term PER < Target PER throughout the run."),(0,i.kt)("li",{parentName:"ul"},"Short term PER < 1%+Target PER throughout the run."),(0,i.kt)("li",{parentName:"ul"},"The combined throughput from both DN-CN1 and CN-CN2 links is effectively\nconstant throughout the run.")),(0,i.kt)("h3",{id:"puma_rf_la-31-point-to-point-link-survivability-with-high-attenuation-and-traffic"},(0,i.kt)("inlineCode",{parentName:"h3"},"PUMA_RF_LA-3.1")," Point-to-Point Link Survivability with High Attenuation and Traffic"),(0,i.kt)("p",null,"Description: The purpose of this test to ensure that LA quickly adapts the MCS\nin response to high attenuation and maintains PER within the acceptable range.\nThis tests how well outer loop of LA uses PER to quickly adapt the MCS, even if\nthe true STF SNR on the link hasn't been communicated back to the transmitter\nwithin a BWGD."),(0,i.kt)("p",null,"Test Setup: P2P setup"),(0,i.kt)("p",null,"Procedure:"),(0,i.kt)("ul",null,(0,i.kt)("li",{parentName:"ul"},"Program attenuator with 0 dB attenuation."),(0,i.kt)("li",{parentName:"ul"},"Reboot both TGs, the DN and the CN."),(0,i.kt)("li",{parentName:"ul"},"On both the DN and CN1, update ",(0,i.kt)("inlineCode",{parentName:"li"},"/etc/e2e_config/fw_cfg.json")," to reflect the\nfollowing:",(0,i.kt)("ul",{parentName:"li"},(0,i.kt)("li",{parentName:"ul"},"Disable TPC."))),(0,i.kt)("li",{parentName:"ul"},"Init and Config FW on DN and CN."),(0,i.kt)("li",{parentName:"ul"},"Associate both DN and CN."),(0,i.kt)("li",{parentName:"ul"},"Ping DN \u2192 CN and CN \u2192 DN to validate connectivity."),(0,i.kt)("li",{parentName:"ul"},"Run iPerf (on the TG) in the background with the following parameters:",(0,i.kt)("ul",{parentName:"li"},(0,i.kt)("li",{parentName:"ul"},"2 Gbps of UDP traffic (bi-directional)"),(0,i.kt)("li",{parentName:"ul"},"Packet size of 1500 bytes"))),(0,i.kt)("li",{parentName:"ul"},"Every 10 seconds, increase and then immediately decrease attenuation, using\nAttenMax computed in the previous step. Repeat this for 100 iterations."),(0,i.kt)("li",{parentName:"ul"},"Terminate iPerf after going through all iterations")),(0,i.kt)("table",null,(0,i.kt)("thead",{parentName:"table"},(0,i.kt)("tr",{parentName:"thead"},(0,i.kt)("th",{parentName:"tr",align:null},"Test ID"),(0,i.kt)("th",{parentName:"tr",align:null},"Min Expected SNR (dB) (greater than)"),(0,i.kt)("th",{parentName:"tr",align:null},"Expected Final MCS"),(0,i.kt)("th",{parentName:"tr",align:null},"Max PER due to Attenuation"),(0,i.kt)("th",{parentName:"tr",align:null},"MAX Time to Reach expected MCS (ms)"))),(0,i.kt)("tbody",{parentName:"table"},(0,i.kt)("tr",{parentName:"tbody"},(0,i.kt)("td",{parentName:"tr",align:null},"LA-3.1.1"),(0,i.kt)("td",{parentName:"tr",align:null},"10"),(0,i.kt)("td",{parentName:"tr",align:null},"8"),(0,i.kt)("td",{parentName:"tr",align:null},"< 1%+Target PER"),(0,i.kt)("td",{parentName:"tr",align:null},"102.4")),(0,i.kt)("tr",{parentName:"tbody"},(0,i.kt)("td",{parentName:"tr",align:null},"LA-3.1.2"),(0,i.kt)("td",{parentName:"tr",align:null},"6.5"),(0,i.kt)("td",{parentName:"tr",align:null},"6"),(0,i.kt)("td",{parentName:"tr",align:null},"< 1%+Target PER"),(0,i.kt)("td",{parentName:"tr",align:null},"102.4")),(0,i.kt)("tr",{parentName:"tbody"},(0,i.kt)("td",{parentName:"tr",align:null},"LA-3.1.3"),(0,i.kt)("td",{parentName:"tr",align:null},"5.5"),(0,i.kt)("td",{parentName:"tr",align:null},"4"),(0,i.kt)("td",{parentName:"tr",align:null},"< 1%+Target PER"),(0,i.kt)("td",{parentName:"tr",align:null},"102.4")))),(0,i.kt)("p",null,"Pass/Fail Criterion:"),(0,i.kt)("ul",null,(0,i.kt)("li",{parentName:"ul"},"Long term PER < Target PER throughout the run."),(0,i.kt)("li",{parentName:"ul"},"Short term PER < 1%+Target PER throughout the run."),(0,i.kt)("li",{parentName:"ul"},"LA's convergence time to expected MCS < 4 BWGDs (i.e. 102.4ms).")),(0,i.kt)("h3",{id:"puma_rf_la-32-point-to-multi-point-link-survivability-with-high-attenuation-and-traffic"},(0,i.kt)("inlineCode",{parentName:"h3"},"PUMA_RF_LA-3.2")," Point-to-Multi-Point Link Survivability with High Attenuation and traffic"),(0,i.kt)("p",null,"Description: The purpose of this test to ensure that LA quickly adapts the MCS\nin response to high attenuation and maintains PER within the acceptable range."),(0,i.kt)("p",null,"Test Setup: P2MP-2 setup"),(0,i.kt)("p",null,"Procedure:"),(0,i.kt)("ul",null,(0,i.kt)("li",{parentName:"ul"},"Program attenuator with 0 dB attenuation."),(0,i.kt)("li",{parentName:"ul"},"Reboot both TGs, the DN and the CNs."),(0,i.kt)("li",{parentName:"ul"},"On both the DN, CN1 and CN2, update ",(0,i.kt)("inlineCode",{parentName:"li"},"/etc/e2e_config/fw_cfg.json")," to reflect\nthe following:",(0,i.kt)("ul",{parentName:"li"},(0,i.kt)("li",{parentName:"ul"},"Disable TPC."))),(0,i.kt)("li",{parentName:"ul"},"Init and Config FW on DN, CN1, and CN2."),(0,i.kt)("li",{parentName:"ul"},"Associate both DN and CN1 and DN and CN2."),(0,i.kt)("li",{parentName:"ul"},"Ping DN \u2192 CN1 and CN1 \u2192 DN to validate connectivity."),(0,i.kt)("li",{parentName:"ul"},"Ping DN \u2192 CN2 and CN2 \u2192 DN to validate connectivity."),(0,i.kt)("li",{parentName:"ul"},"Run iPerf (on the TG) between DN \u2192 CN2 and DN \u2192 CN1 with the following\nparameters:",(0,i.kt)("ul",{parentName:"li"},(0,i.kt)("li",{parentName:"ul"},"2 Gbps of UDP traffic (bi-directional)"),(0,i.kt)("li",{parentName:"ul"},"Packet size of 1500 bytes"))),(0,i.kt)("li",{parentName:"ul"},"Every 10 seconds, increase and then immediately decrease attenuation on\nDN-CN1, similar to how it is done in LA-3.1. Repeat this for 100 iterations."),(0,i.kt)("li",{parentName:"ul"},"Terminate iPerf after going through all iterations.")),(0,i.kt)("p",null,"Pass/Fail Criterion:"),(0,i.kt)("ul",null,(0,i.kt)("li",{parentName:"ul"},"There is no impact to throughput on DN-CN2 due to attenuation on DN-CN1."),(0,i.kt)("li",{parentName:"ul"},"Long term PER < Target PER throughout the run."),(0,i.kt)("li",{parentName:"ul"},"Short term PER < 1%+Target PER throughout the run."),(0,i.kt)("li",{parentName:"ul"},"LA's convergence time to expected MCS < 4 BWGDs (i.e. 102.4ms).")),(0,i.kt)("h3",{id:"puma_rf_la-33-stability-of-link-adaptation-to-small-scale-fades"},(0,i.kt)("inlineCode",{parentName:"h3"},"PUMA_RF_LA-3.3")," Stability of Link Adaptation to small scale fades"),(0,i.kt)("p",null,"Description: The purpose of this test is to check the hysteresis in Link\nAdaptation, by simulating +/- 2 dB fades close to the operational limit of any\ngiven MCS."),(0,i.kt)("p",null,"Test Setup: P2P setup"),(0,i.kt)("p",null,"Procedure:"),(0,i.kt)("ul",null,(0,i.kt)("li",{parentName:"ul"},"Program attenuator with 0 dB attenuation."),(0,i.kt)("li",{parentName:"ul"},"Reboot both TGs, the DN and the CN."),(0,i.kt)("li",{parentName:"ul"},"For each MCSx in the set {6, 9, 10, 11, 12}, repeat the following tests:"),(0,i.kt)("li",{parentName:"ul"},"On both the DN and CN, update ",(0,i.kt)("inlineCode",{parentName:"li"},"/etc/e2e_config/fw_cfg.json")," to reflect the\nfollowing:",(0,i.kt)("ul",{parentName:"li"},(0,i.kt)("li",{parentName:"ul"},"Disable TPC."))),(0,i.kt)("li",{parentName:"ul"},"Init and Config FW on DN and CN."),(0,i.kt)("li",{parentName:"ul"},"Associate both DN and CN."),(0,i.kt)("li",{parentName:"ul"},"Ping DN \u2192 CN and CN \u2192 DN to validate connectivity."),(0,i.kt)("li",{parentName:"ul"},"Measure STF SNR on the link and compute median link SNR."),(0,i.kt)("li",{parentName:"ul"},"Program the attenuator to ensure that STF SNR is at least 2dB above the min\nSNR for MCSx (see Table 1)."),(0,i.kt)("li",{parentName:"ul"},"Run iPerf (on the TG) in the background with the following parameters:",(0,i.kt)("ul",{parentName:"li"},(0,i.kt)("li",{parentName:"ul"},"2 Gbps of UDP traffic (bi-directional)"),(0,i.kt)("li",{parentName:"ul"},"Packet size of 1500 bytes"))),(0,i.kt)("li",{parentName:"ul"},"Every 2 seconds, increase and immediately decrease the attenuation by 1 dB on\nDN-CN and continue this for 100 iterations."),(0,i.kt)("li",{parentName:"ul"},"Terminate iPerf after going through all attenuations")),(0,i.kt)("p",null,"Pass/Fail Criterion:"),(0,i.kt)("ul",null,(0,i.kt)("li",{parentName:"ul"},"LA maintains the MCS and does not oscillate between two MCSes for the +/- 1dB\nattenuations on the DN-CN link."),(0,i.kt)("li",{parentName:"ul"},"Long term PER < Target PER throughout the run."),(0,i.kt)("li",{parentName:"ul"},"Short term PER < 1%+Target PER throughout the run.")),(0,i.kt)("h3",{id:"puma_rf_la-40-stability-of-link-adaptation-across-the-range-of-snrs"},(0,i.kt)("inlineCode",{parentName:"h3"},"PUMA_RF_LA-4.0")," Stability of Link Adaptation across the range of SNRs"),(0,i.kt)("p",null,"Description: The purpose of this test is to check whether hysteresis in Link\nAdaptation is functioning correctly and prevents oscillations across the entire\noperational range of SNR values."),(0,i.kt)("p",null,"Test Setup: P2P setup"),(0,i.kt)("p",null,"Procedure:"),(0,i.kt)("ul",null,(0,i.kt)("li",{parentName:"ul"},"Program attenuator with 0 dB attenuation."),(0,i.kt)("li",{parentName:"ul"},"Reboot both TGs, the DN and the CN."),(0,i.kt)("li",{parentName:"ul"},"On both the DN and CN1, update ",(0,i.kt)("inlineCode",{parentName:"li"},"/etc/e2e_config/fw_cfg.json")," to reflect the\nfollowing:",(0,i.kt)("ul",{parentName:"li"},(0,i.kt)("li",{parentName:"ul"},"Disable TPC."))),(0,i.kt)("li",{parentName:"ul"},"Init and Config FW on DN and CN1."),(0,i.kt)("li",{parentName:"ul"},"Associate both DN and CN1."),(0,i.kt)("li",{parentName:"ul"},"Ping DN \u2192 CN1 and CN1 \u2192 DN to validate connectivity."),(0,i.kt)("li",{parentName:"ul"},"Measure STF SNR on the link and compute median link SNR."),(0,i.kt)("li",{parentName:"ul"},"Program attenuation limit for DN-CN1 (i.e. AttenMax) to ensure STF SNR is no\nless than 2 dB."),(0,i.kt)("li",{parentName:"ul"},"Run iPerf (on the TG) in the background with the following parameters:",(0,i.kt)("ul",{parentName:"li"},(0,i.kt)("li",{parentName:"ul"},"2 Gbps of UDP traffic (bi-directional)"),(0,i.kt)("li",{parentName:"ul"},"Packet size of 1500 bytes"))),(0,i.kt)("li",{parentName:"ul"},"Every 60 seconds, increase the attenuation by 0.25 dB on DN-CN1 and continue\nuntil AttenMax is reached on DN-CN1."),(0,i.kt)("li",{parentName:"ul"},"Every 60 seconds, decrease the attenuation by 0.25 dB on DN-CN1 and continue\nuntil attenuator value of 0 is reached on the DN-CN1 link."),(0,i.kt)("li",{parentName:"ul"},"Terminate iPerf after going through all attenuations")),(0,i.kt)("p",null,"Pass/Fail Criterion:"),(0,i.kt)("ul",null,(0,i.kt)("li",{parentName:"ul"},"LA does not oscillate between two MCSes for any programmed value for\nattenuation on DN-CN1."),(0,i.kt)("li",{parentName:"ul"},"Long term PER < Target PER throughout the run."),(0,i.kt)("li",{parentName:"ul"},"Short term PER < 1%+Target PER throughout the run.")),(0,i.kt)("h3",{id:"puma_rf_la-41-point-to-point-link-ramp-test-for-tpc"},(0,i.kt)("inlineCode",{parentName:"h3"},"PUMA_RF_LA-4.1")," Point-to-Point Link RAMP TEST for TPC"),(0,i.kt)("p",null,"Description: The purpose of this test to check whether TPC adapts the Tx Power\nto maintain the target SNR on the link. Attenuation is adjusted 1 dB / second,\nto allow TPC to adapt to the change without causing any PER on the link."),(0,i.kt)("p",null,"Test Setup: LA-TB-1 setup"),(0,i.kt)("p",null,"Procedure:"),(0,i.kt)("ul",null,(0,i.kt)("li",{parentName:"ul"},"Program attenuator with 0 dB attenuation."),(0,i.kt)("li",{parentName:"ul"},"Reboot both TGs, the DN and the CN1."),(0,i.kt)("li",{parentName:"ul"},"Init and Config FW on DN and CN."),(0,i.kt)("li",{parentName:"ul"},"Associate both DN and CN."),(0,i.kt)("li",{parentName:"ul"},"Ping DN \u2192 CN and CN \u2192 DN to validate connectivity."),(0,i.kt)("li",{parentName:"ul"},"Sample the STF SNR on the link and program attenuator to bring STF SNR to 15\ndB, if it isn't already."),(0,i.kt)("li",{parentName:"ul"},"Sample the Tx Power on the link and record this value (currTxPower)."),(0,i.kt)("li",{parentName:"ul"},"Run iPerf (on the TG) in the background with the following parameters:",(0,i.kt)("ul",{parentName:"li"},(0,i.kt)("li",{parentName:"ul"},"2 Gbps of UDP traffic (bi-directional)"),(0,i.kt)("li",{parentName:"ul"},"Packet size of 1500 bytes"))),(0,i.kt)("li",{parentName:"ul"},"Every 30 seconds, increase the attenuation by 0.5 dB and continue to do so for\n2*(MaxPower - currTxPower) steps."),(0,i.kt)("li",{parentName:"ul"},"Terminate iPerf after going through all attenuations")),(0,i.kt)("p",null,"Pass/Fail Criterion:"),(0,i.kt)("ul",null,(0,i.kt)("li",{parentName:"ul"},"TPC maintains the target STF SNR of 15 dB throughout the test."),(0,i.kt)("li",{parentName:"ul"},"Long term PER < Target PER throughout the run."),(0,i.kt)("li",{parentName:"ul"},"Short term PER < 1%+Target PER throughout the run."),(0,i.kt)("li",{parentName:"ul"},"LA is able to maintain MCS 9 the test.")),(0,i.kt)("h3",{id:"puma_rf_la-42-point-to-point-link-high-attenuation-test-for-tpc"},(0,i.kt)("inlineCode",{parentName:"h3"},"PUMA_RF_LA-4.2")," Point-to-Point Link high attenuation TEST for TPC"),(0,i.kt)("p",null,"Description: This test is intended to assess TPC's ability to handle foliage\nrelated impairments on the link and adjusting Transmit Power to account for deep\nfades introduced on the link."),(0,i.kt)("p",null,"Test Setup: P2P setup"),(0,i.kt)("p",null,"Procedure:"),(0,i.kt)("ul",null,(0,i.kt)("li",{parentName:"ul"},"Program attenuator with 0 dB attenuation."),(0,i.kt)("li",{parentName:"ul"},"Reboot both TGs, the DN and the CN."),(0,i.kt)("li",{parentName:"ul"},"Init and Config FW on DN and CN."),(0,i.kt)("li",{parentName:"ul"},"Associate both DN and CN."),(0,i.kt)("li",{parentName:"ul"},"Ping DN \u2192 CN and CN \u2192 DN to validate connectivity."),(0,i.kt)("li",{parentName:"ul"},"Sample the Tx Power on the link and record this value (currTxPower)."),(0,i.kt)("li",{parentName:"ul"},"Run iPerf (on the TG) in the background with the following parameters:",(0,i.kt)("ul",{parentName:"li"},(0,i.kt)("li",{parentName:"ul"},"2 Gbps of UDP traffic (bi-directional)"),(0,i.kt)("li",{parentName:"ul"},"Packet size of 1500 bytes"))),(0,i.kt)("li",{parentName:"ul"},"Every 60 seconds, increase and then immediately decrease attenuation for a\ntotal of 3-10 iterations (picked uniformly at random), using the attenuation\nvalues in the range ","[0, MaxPower - currTxPower]",". Repeat this for 30\niterations."),(0,i.kt)("li",{parentName:"ul"},"Terminate iPerf after going through all iterations")),(0,i.kt)("p",null,"Pass/Fail Criterion:"),(0,i.kt)("ul",null,(0,i.kt)("li",{parentName:"ul"},"TPC adapts to using high TX Power in response to first attenuation sequence\nand maintains that for the rest of the test run."),(0,i.kt)("li",{parentName:"ul"},"Long term PER < Target PER throughout the run."),(0,i.kt)("li",{parentName:"ul"},"Short term PER < 1%+Target PER throughout the run.")))}h.isMDXComponent=!0}}]);