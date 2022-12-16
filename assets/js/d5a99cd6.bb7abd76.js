"use strict";(self.webpackChunkdocusaurus=self.webpackChunkdocusaurus||[]).push([[606],{3905:(e,t,a)=>{a.d(t,{Zo:()=>u,kt:()=>k});var n=a(7294);function l(e,t,a){return t in e?Object.defineProperty(e,t,{value:a,enumerable:!0,configurable:!0,writable:!0}):e[t]=a,e}function i(e,t){var a=Object.keys(e);if(Object.getOwnPropertySymbols){var n=Object.getOwnPropertySymbols(e);t&&(n=n.filter((function(t){return Object.getOwnPropertyDescriptor(e,t).enumerable}))),a.push.apply(a,n)}return a}function r(e){for(var t=1;t<arguments.length;t++){var a=null!=arguments[t]?arguments[t]:{};t%2?i(Object(a),!0).forEach((function(t){l(e,t,a[t])})):Object.getOwnPropertyDescriptors?Object.defineProperties(e,Object.getOwnPropertyDescriptors(a)):i(Object(a)).forEach((function(t){Object.defineProperty(e,t,Object.getOwnPropertyDescriptor(a,t))}))}return e}function s(e,t){if(null==e)return{};var a,n,l=function(e,t){if(null==e)return{};var a,n,l={},i=Object.keys(e);for(n=0;n<i.length;n++)a=i[n],t.indexOf(a)>=0||(l[a]=e[a]);return l}(e,t);if(Object.getOwnPropertySymbols){var i=Object.getOwnPropertySymbols(e);for(n=0;n<i.length;n++)a=i[n],t.indexOf(a)>=0||Object.prototype.propertyIsEnumerable.call(e,a)&&(l[a]=e[a])}return l}var o=n.createContext({}),p=function(e){var t=n.useContext(o),a=t;return e&&(a="function"==typeof e?e(t):r(r({},t),e)),a},u=function(e){var t=p(e.components);return n.createElement(o.Provider,{value:t},e.children)},c={inlineCode:"code",wrapper:function(e){var t=e.children;return n.createElement(n.Fragment,{},t)}},d=n.forwardRef((function(e,t){var a=e.components,l=e.mdxType,i=e.originalType,o=e.parentName,u=s(e,["components","mdxType","originalType","parentName"]),d=p(a),k=l,m=d["".concat(o,".").concat(k)]||d[k]||c[k]||i;return a?n.createElement(m,r(r({ref:t},u),{},{components:a})):n.createElement(m,r({ref:t},u))}));function k(e,t){var a=arguments,l=t&&t.mdxType;if("string"==typeof e||l){var i=a.length,r=new Array(i);r[0]=d;var s={};for(var o in t)hasOwnProperty.call(t,o)&&(s[o]=t[o]);s.originalType=e,s.mdxType="string"==typeof e?e:l,r[1]=s;for(var p=2;p<i;p++)r[p]=a[p];return n.createElement.apply(null,r)}return n.createElement.apply(null,a)}d.displayName="MDXCreateElement"},8727:(e,t,a)=>{a.r(t),a.d(t,{assets:()=>o,contentTitle:()=>r,default:()=>c,frontMatter:()=>i,metadata:()=>s,toc:()=>p});var n=a(7462),l=(a(7294),a(3905));const i={},r="WSEC (WPA-PSK) Tests",s={unversionedId:"tests/WSEC",id:"tests/WSEC",title:"WSEC (WPA-PSK) Tests",description:"The WSEC tests validate Over-The-Air Security with WPA-PSK.",source:"@site/../docs/tests/WSEC.md",sourceDirName:"tests",slug:"/tests/WSEC",permalink:"/terragraph-ctf/tests/WSEC",draft:!1,editUrl:"https://github.com/terragraph/terragraph-ctf/edit/main/docs/../docs/tests/WSEC.md",tags:[],version:"current",frontMatter:{},sidebar:"docs",previous:{title:"802.1X Tests",permalink:"/terragraph-ctf/tests/802.1X"},next:{title:"Link Level Scheduler Tests",permalink:"/terragraph-ctf/tests/LLS"}},o={},p=[{value:"Base Feature Validation",id:"base-feature-validation",level:2},{value:"<code>WSEC-0-1</code> Pass-phrase mismatch",id:"wsec-0-1-pass-phrase-mismatch",level:3},{value:"Ignition Test Cases",id:"ignition-test-cases",level:2},{value:"<code>WSEC-1</code> 1DN+7CN Association (SAME Passphrase on all links)",id:"wsec-1-1dn7cn-association-same-passphrase-on-all-links",level:3},{value:"<code>WSEC-2</code> 1DN+6CN+1DN Association",id:"wsec-2-1dn6cn1dn-association",level:3},{value:"<code>WSEC-3</code> 1DN+5CN+2DN Association",id:"wsec-3-1dn5cn2dn-association",level:3},{value:"<code>WSEC-4</code> 1DN+5CN+2DN Association (Reverse Polarity, Reverse disassoc)",id:"wsec-4-1dn5cn2dn-association-reverse-polarity-reverse-disassoc",level:3},{value:"<code>WSEC-5</code> Reassoc Stress Test",id:"wsec-5-reassoc-stress-test",level:3},{value:"<code>WSEC-6</code> Bring-up RF Butterfly",id:"wsec-6-bring-up-rf-butterfly",level:3},{value:"Throughput Test Cases",id:"throughput-test-cases",level:2}],u={toc:p};function c(e){let{components:t,...a}=e;return(0,l.kt)("wrapper",(0,n.Z)({},u,a,{components:t,mdxType:"MDXLayout"}),(0,l.kt)("h1",{id:"wsec-wpa-psk-tests"},"WSEC (WPA-PSK) Tests"),(0,l.kt)("p",null,"The WSEC tests validate Over-The-Air Security with WPA-PSK."),(0,l.kt)("h2",{id:"base-feature-validation"},"Base Feature Validation"),(0,l.kt)("p",null,"It's important to run through some negative tests, to ensure that the state\nmachine for the security feature is properly exercised and works as expected in\nall such conditions. We've determined the following negative tests for feature\nvalidation:"),(0,l.kt)("ul",null,(0,l.kt)("li",{parentName:"ul"},"Pass-phrase mismatch on opposite ends of the link"),(0,l.kt)("li",{parentName:"ul"},"Termination of ",(0,l.kt)("inlineCode",{parentName:"li"},"hostapd"),"/",(0,l.kt)("inlineCode",{parentName:"li"},"wpa_supplicant"))),(0,l.kt)("h3",{id:"wsec-0-1-pass-phrase-mismatch"},(0,l.kt)("inlineCode",{parentName:"h3"},"WSEC-0-1")," Pass-phrase mismatch"),(0,l.kt)("p",null,"Description: For the aforementioned negative tests, we plan to use two P2P\nscenarios (DN-CN and DN-DN). The test details for each of the above negative\ntests are listed below."),(0,l.kt)("p",null,"Procedure and validation: For each P2P scenario (DN-DN and DN-CN), do the\nfollowing:"),(0,l.kt)("ol",null,(0,l.kt)("li",{parentName:"ol"},"On the initiator DN, edit wpa_passphrase field in\n",(0,l.kt)("inlineCode",{parentName:"li"},"/etc/hostapd/hostapd_terra0.conf"),' from "psk_test" to "psk2_test".'),(0,l.kt)("li",{parentName:"ol"},"Follow the steps in WSEC-1 and validate that link-up fails."),(0,l.kt)("li",{parentName:"ol"},'Revert step 1, i.e. restore wpa_passphrase field to "psk_test".'),(0,l.kt)("li",{parentName:"ol"},"Validate that the link-up succeeds."),(0,l.kt)("li",{parentName:"ol"},"Reboot all the nodes."),(0,l.kt)("li",{parentName:"ol"},"On the responder DN/CN, edit psk field in\n",(0,l.kt)("inlineCode",{parentName:"li"},"/etc/wpa_supplicant/wpa_supplicant_terra0.conf"),' from "psk_test" to\n"psk2_test".'),(0,l.kt)("li",{parentName:"ol"},"Follow the steps in WSEC-1 and validate that link-up fails."),(0,l.kt)("li",{parentName:"ol"},'Revert step 6, i.e. restore psk field to "psk_test".'),(0,l.kt)("li",{parentName:"ol"},"Validate that the link-up succeeds.")),(0,l.kt)("h2",{id:"ignition-test-cases"},"Ignition Test Cases"),(0,l.kt)("h3",{id:"wsec-1-1dn7cn-association-same-passphrase-on-all-links"},(0,l.kt)("inlineCode",{parentName:"h3"},"WSEC-1")," 1DN+7CN Association (SAME Passphrase on all links)"),(0,l.kt)("p",null,"Procedure:"),(0,l.kt)("ul",null,(0,l.kt)("li",{parentName:"ul"},"Ignite the network for this topology, using the appropriate topology file."),(0,l.kt)("li",{parentName:"ul"},"Ping each link using link local and verify it has come up."),(0,l.kt)("li",{parentName:"ul"},"Send 100Mbps bidirectional iPerf UDP traffic simultaneously on all interfaces\nfrom traffic generators."),(0,l.kt)("li",{parentName:"ul"},"Execute the following E2E commands:",(0,l.kt)("ol",{parentName:"li"},(0,l.kt)("li",{parentName:"ol"},(0,l.kt)("inlineCode",{parentName:"li"},'tg config modify network -i "radioParamsBase.fwParams.wsecEnable" 1')),(0,l.kt)("li",{parentName:"ol"},"Output of the security application is redirected. Please check files like\n",(0,l.kt)("inlineCode",{parentName:"li"},"/tmp/hostapd_terra0")," and ",(0,l.kt)("inlineCode",{parentName:"li"},"/tmp/wpa_supplicant_terra0"),"."))),(0,l.kt)("li",{parentName:"ul"},"Ping each link using link local and verify it has come up."),(0,l.kt)("li",{parentName:"ul"},"Send 100Mbps bidirectional iPerf UDP traffic simultaneously on all interfaces\nfrom traffic generators.")),(0,l.kt)("p",null,"Validation:"),(0,l.kt)("ul",null,(0,l.kt)("li",{parentName:"ul"},"All Associations succeed."),(0,l.kt)("li",{parentName:"ul"},"Ping success"),(0,l.kt)("li",{parentName:"ul"},"No packet loss."),(0,l.kt)("li",{parentName:"ul"},"In all case, iPerf throughput of 100Mbps is achieved on each link")),(0,l.kt)("h3",{id:"wsec-2-1dn6cn1dn-association"},(0,l.kt)("inlineCode",{parentName:"h3"},"WSEC-2")," 1DN+6CN+1DN Association"),(0,l.kt)("p",null,"Procedure:"),(0,l.kt)("ul",null,(0,l.kt)("li",{parentName:"ul"},"Same as ",(0,l.kt)("inlineCode",{parentName:"li"},"WSEC-1"),", but assign DN role in topology file to one of the 7 peers.")),(0,l.kt)("h3",{id:"wsec-3-1dn5cn2dn-association"},(0,l.kt)("inlineCode",{parentName:"h3"},"WSEC-3")," 1DN+5CN+2DN Association"),(0,l.kt)("p",null,"Procedure:"),(0,l.kt)("ul",null,(0,l.kt)("li",{parentName:"ul"},"Same as ",(0,l.kt)("inlineCode",{parentName:"li"},"WSEC-1"),", but assign DN role in topology file to two of the 7 peers.")),(0,l.kt)("h3",{id:"wsec-4-1dn5cn2dn-association-reverse-polarity-reverse-disassoc"},(0,l.kt)("inlineCode",{parentName:"h3"},"WSEC-4")," 1DN+5CN+2DN Association (Reverse Polarity, Reverse disassoc)"),(0,l.kt)("p",null,"Procedure:"),(0,l.kt)("ul",null,(0,l.kt)("li",{parentName:"ul"},"Same as ",(0,l.kt)("inlineCode",{parentName:"li"},"WSEC-3"),", but use flip the polarity on each sector.")),(0,l.kt)("h3",{id:"wsec-5-reassoc-stress-test"},(0,l.kt)("inlineCode",{parentName:"h3"},"WSEC-5")," Reassoc Stress Test"),(0,l.kt)("p",null,"Procedure:"),(0,l.kt)("ul",null,(0,l.kt)("li",{parentName:"ul"},"Randomly select a peer"),(0,l.kt)("li",{parentName:"ul"},"Toggle linkup state between initiator and peer, using attenuator cabled to the\nlink."),(0,l.kt)("li",{parentName:"ul"},"After linkup, ping the peer."),(0,l.kt)("li",{parentName:"ul"},"Repeat these steps 50 times.")),(0,l.kt)("p",null,"Validation:"),(0,l.kt)("ul",null,(0,l.kt)("li",{parentName:"ul"},"No crashes."),(0,l.kt)("li",{parentName:"ul"},"All pings succeed.")),(0,l.kt)("h3",{id:"wsec-6-bring-up-rf-butterfly"},(0,l.kt)("inlineCode",{parentName:"h3"},"WSEC-6")," Bring-up RF Butterfly"),(0,l.kt)("p",null,"Test Setup: Butterfly test setup"),(0,l.kt)("p",null,"Procedure:"),(0,l.kt)("ul",null,(0,l.kt)("li",{parentName:"ul"},"Ignite the network for this topology, using the appropriate topology file."),(0,l.kt)("li",{parentName:"ul"},"Ping each link using link local and verify it has come up."),(0,l.kt)("li",{parentName:"ul"},"Send 100Mbps bidirectional iPerf UDP traffic simultaneously on all interfaces\nfrom traffic generators."),(0,l.kt)("li",{parentName:"ul"},"Execute the following E2E commands:",(0,l.kt)("ol",{parentName:"li"},(0,l.kt)("li",{parentName:"ol"},(0,l.kt)("inlineCode",{parentName:"li"},'tg config modify network -i "radioParamsBase.fwParams.wsecEnable" 1')),(0,l.kt)("li",{parentName:"ol"},"Output of the security application is redirected. Please check files like\n",(0,l.kt)("inlineCode",{parentName:"li"},"/tmp/hostapd_terra0")," and ",(0,l.kt)("inlineCode",{parentName:"li"},"/tmp/wpa_supplicant_terra0"),"."))),(0,l.kt)("li",{parentName:"ul"},"Ping each link using link local and verify it has come up."),(0,l.kt)("li",{parentName:"ul"},"Send 100Mbps bidirectional iPerf UDP traffic simultaneously on all interfaces\nfrom traffic generators.")),(0,l.kt)("p",null,"Validation:"),(0,l.kt)("ul",null,(0,l.kt)("li",{parentName:"ul"},"All Associations succeed."),(0,l.kt)("li",{parentName:"ul"},"Ping success"),(0,l.kt)("li",{parentName:"ul"},"No packet loss."),(0,l.kt)("li",{parentName:"ul"},"iPerf throughput of 100Mbps is achieved on each link."),(0,l.kt)("li",{parentName:"ul"},"Disassociation success.")),(0,l.kt)("h2",{id:"throughput-test-cases"},"Throughput Test Cases"),(0,l.kt)("p",null,"Description: These test cases are purposed to evaluate the performance impact of\nenabling OTA security in topological scenarios."),(0,l.kt)("table",null,(0,l.kt)("thead",{parentName:"table"},(0,l.kt)("tr",{parentName:"thead"},(0,l.kt)("th",{parentName:"tr",align:null},"Test ID"),(0,l.kt)("th",{parentName:"tr",align:null},"Topology"),(0,l.kt)("th",{parentName:"tr",align:null},"Packet Size (bytes)"),(0,l.kt)("th",{parentName:"tr",align:null},"UDP Push Rate (Mbps) - laMaxMcs = 9"),(0,l.kt)("th",{parentName:"tr",align:null},"UDP Expected Throughput (Mbps)"),(0,l.kt)("th",{parentName:"tr",align:null},"UDP Push Rate (Mbps) - laMaxMcs = 12"),(0,l.kt)("th",{parentName:"tr",align:null},"UDP Expected Throughput (Mbps)"))),(0,l.kt)("tbody",{parentName:"table"},(0,l.kt)("tr",{parentName:"tbody"},(0,l.kt)("td",{parentName:"tr",align:null},"WSEC-12"),(0,l.kt)("td",{parentName:"tr",align:null},"Butterfly (2DNs, 2 CNs per DN)"),(0,l.kt)("td",{parentName:"tr",align:null},"5602(MCS9)/ 5469(MCS12)"),(0,l.kt)("td",{parentName:"tr",align:null},"900(serial)/ 320(parallel)"),(0,l.kt)("td",{parentName:"tr",align:null},"891.90(serial)/ 302.59(parallel)"),(0,l.kt)("td",{parentName:"tr",align:null},"900(serial)/ 320(parallel)"),(0,l.kt)("td",{parentName:"tr",align:null},"891.90(serial)/ 302.59(parallel)")),(0,l.kt)("tr",{parentName:"tbody"},(0,l.kt)("td",{parentName:"tr",align:null},"WSEC-13"),(0,l.kt)("td",{parentName:"tr",align:null},"Y-street (3 DNs only)"),(0,l.kt)("td",{parentName:"tr",align:null},"5602(MCS9)/ 5469(MCS12)"),(0,l.kt)("td",{parentName:"tr",align:null},"900(serial)/ 450(parallel)"),(0,l.kt)("td",{parentName:"tr",align:null},"891.90(serial)/ 441(parallel)"),(0,l.kt)("td",{parentName:"tr",align:null},"1420(serial)/ 770(parallel)"),(0,l.kt)("td",{parentName:"tr",align:null},"1405.84(serial)/ 765.16(parallel)")),(0,l.kt)("tr",{parentName:"tbody"},(0,l.kt)("td",{parentName:"tr",align:null},"WSEC-14"),(0,l.kt)("td",{parentName:"tr",align:null},"Figure of U"),(0,l.kt)("td",{parentName:"tr",align:null},"5602(MCS9)/ 5469(MCS12)"),(0,l.kt)("td",{parentName:"tr",align:null},"1050"),(0,l.kt)("td",{parentName:"tr",align:null},"1000"),(0,l.kt)("td",{parentName:"tr",align:null},"1650"),(0,l.kt)("td",{parentName:"tr",align:null},"1610")))),(0,l.kt)("p",null,(0,l.kt)("strong",{parentName:"p"},"Note:")," Due to setup limitations/availability, throughput numbers might have\nto be adjusted."),(0,l.kt)("p",null,"Procedure:"),(0,l.kt)("ul",null,(0,l.kt)("li",{parentName:"ul"},"Ignite topology for the test ID shown in the table above."),(0,l.kt)("li",{parentName:"ul"},"Ping each link using link local."),(0,l.kt)("li",{parentName:"ul"},"Send iPerf UDP traffic serially on each link from traffic generators, using\nthe push rate provided in the table above."),(0,l.kt)("li",{parentName:"ul"},"Send iPerf UDP traffic simultaneously on all links from traffic generators (if\napplicable), using the push rate provided in the table above.")),(0,l.kt)("p",null,"Validation:"),(0,l.kt)("ul",null,(0,l.kt)("li",{parentName:"ul"},"All Associations succeed for the ignited topology."),(0,l.kt)("li",{parentName:"ul"},"Ping success on all links."),(0,l.kt)("li",{parentName:"ul"},"iPerf throughput is within 95% expected throughput, as shown in the table\nabove.")))}c.isMDXComponent=!0}}]);