"use strict";(self.webpackChunkdocusaurus=self.webpackChunkdocusaurus||[]).push([[679],{3905:(e,t,n)=>{n.d(t,{Zo:()=>u,kt:()=>d});var r=n(7294);function a(e,t,n){return t in e?Object.defineProperty(e,t,{value:n,enumerable:!0,configurable:!0,writable:!0}):e[t]=n,e}function l(e,t){var n=Object.keys(e);if(Object.getOwnPropertySymbols){var r=Object.getOwnPropertySymbols(e);t&&(r=r.filter((function(t){return Object.getOwnPropertyDescriptor(e,t).enumerable}))),n.push.apply(n,r)}return n}function i(e){for(var t=1;t<arguments.length;t++){var n=null!=arguments[t]?arguments[t]:{};t%2?l(Object(n),!0).forEach((function(t){a(e,t,n[t])})):Object.getOwnPropertyDescriptors?Object.defineProperties(e,Object.getOwnPropertyDescriptors(n)):l(Object(n)).forEach((function(t){Object.defineProperty(e,t,Object.getOwnPropertyDescriptor(n,t))}))}return e}function o(e,t){if(null==e)return{};var n,r,a=function(e,t){if(null==e)return{};var n,r,a={},l=Object.keys(e);for(r=0;r<l.length;r++)n=l[r],t.indexOf(n)>=0||(a[n]=e[n]);return a}(e,t);if(Object.getOwnPropertySymbols){var l=Object.getOwnPropertySymbols(e);for(r=0;r<l.length;r++)n=l[r],t.indexOf(n)>=0||Object.prototype.propertyIsEnumerable.call(e,n)&&(a[n]=e[n])}return a}var s=r.createContext({}),p=function(e){var t=r.useContext(s),n=t;return e&&(n="function"==typeof e?e(t):i(i({},t),e)),n},u=function(e){var t=p(e.components);return r.createElement(s.Provider,{value:t},e.children)},m={inlineCode:"code",wrapper:function(e){var t=e.children;return r.createElement(r.Fragment,{},t)}},c=r.forwardRef((function(e,t){var n=e.components,a=e.mdxType,l=e.originalType,s=e.parentName,u=o(e,["components","mdxType","originalType","parentName"]),c=p(n),d=a,k=c["".concat(s,".").concat(d)]||c[d]||m[d]||l;return n?r.createElement(k,i(i({ref:t},u),{},{components:n})):r.createElement(k,i({ref:t},u))}));function d(e,t){var n=arguments,a=t&&t.mdxType;if("string"==typeof e||a){var l=n.length,i=new Array(l);i[0]=c;var o={};for(var s in t)hasOwnProperty.call(t,s)&&(o[s]=t[s]);o.originalType=e,o.mdxType="string"==typeof e?e:a,i[1]=o;for(var p=2;p<l;p++)i[p]=n[p];return r.createElement.apply(null,i)}return r.createElement.apply(null,n)}c.displayName="MDXCreateElement"},7416:(e,t,n)=>{n.r(t),n.d(t,{assets:()=>s,contentTitle:()=>i,default:()=>m,frontMatter:()=>l,metadata:()=>o,toc:()=>p});var r=n(7462),a=(n(7294),n(3905));const l={},i="Throughput Tests",o={unversionedId:"tests/Throughput",id:"tests/Throughput",title:"Throughput Tests",description:"The following will be the tests covered:",source:"@site/../docs/tests/Throughput.md",sourceDirName:"tests",slug:"/tests/Throughput",permalink:"/terragraph-ctf/tests/Throughput",draft:!1,editUrl:"https://github.com/terragraph/terragraph-ctf/edit/main/docs/../docs/tests/Throughput.md",tags:[],version:"current",frontMatter:{},sidebar:"docs",previous:{title:"Association Tests",permalink:"/terragraph-ctf/tests/Association"},next:{title:"Link Adaptation Tests",permalink:"/terragraph-ctf/tests/Link_Adaptation"}},s={},p=[],u={toc:p};function m(e){let{components:t,...n}=e;return(0,a.kt)("wrapper",(0,r.Z)({},u,n,{components:t,mdxType:"MDXLayout"}),(0,a.kt)("h1",{id:"throughput-tests"},"Throughput Tests"),(0,a.kt)("p",null,"The following will be the tests covered:"),(0,a.kt)("ul",null,(0,a.kt)("li",{parentName:"ul"},"P2P tests",(0,a.kt)("ul",{parentName:"li"},(0,a.kt)("li",{parentName:"ul"},"These are configured as ",(0,a.kt)("inlineCode",{parentName:"li"},"TP-P2P.xy")," where ",(0,a.kt)("inlineCode",{parentName:"li"},"x")," is the PCI Generation on one\nside and ",(0,a.kt)("inlineCode",{parentName:"li"},"y")," is the PCI generation on the other side (e.g. ",(0,a.kt)("inlineCode",{parentName:"li"},"TP-TP.32")," is\nsending from sector using PCI Generation 3 to a sector using PCIe\nGeneration 2)"),(0,a.kt)("li",{parentName:"ul"},"TCP, UDP"))),(0,a.kt)("li",{parentName:"ul"},"P2MP tests (TCP, UDP and Imix 500, 1500 are layer 3 packet sizes)",(0,a.kt)("ul",{parentName:"li"},(0,a.kt)("li",{parentName:"ul"},"The P2MP-N tests are configured as follows DN \u2194 {DN, N-1 CNs}"),(0,a.kt)("li",{parentName:"ul"},"Modes",(0,a.kt)("ul",{parentName:"li"},(0,a.kt)("li",{parentName:"ul"},"Burst mode (B)",(0,a.kt)("ul",{parentName:"li"},(0,a.kt)("li",{parentName:"ul"},"All associations made traffic is solely between DN \u2194 DN"))),(0,a.kt)("li",{parentName:"ul"},"Average mode (A)",(0,a.kt)("ul",{parentName:"li"},(0,a.kt)("li",{parentName:"ul"},"All associations made, traffic is evenly distributed between the\nlinks"))),(0,a.kt)("li",{parentName:"ul"},"Overload (O)",(0,a.kt)("ul",{parentName:"li"},(0,a.kt)("li",{parentName:"ul"},"All associations made, traffic is evenly distributed between the\nlinks. We push UDP traffic at 150% of the link capacity"))))))),(0,a.kt)("li",{parentName:"ul"},"Multi Hop test are configured as ",(0,a.kt)("inlineCode",{parentName:"li"},"TP-MH.x")," where ",(0,a.kt)("inlineCode",{parentName:"li"},"x")," is the number of hops\n(TCP, UDP and Imix 500, 1500 and 1150 are layer 3 packet sizes, Test1: UDP &\nTCP 1500 packet size, Test2: UDP & TCP 500 packet size and Imix), Test2: UDP &\nTCP 1150 packet size",(0,a.kt)("ul",{parentName:"li"},(0,a.kt)("li",{parentName:"ul"},"Unidirection Multihop test are configured as ",(0,a.kt)("inlineCode",{parentName:"li"},"TP-MH.x.y.4")," where ",(0,a.kt)("inlineCode",{parentName:"li"},"x")," is\nthe number of hops, ",(0,a.kt)("inlineCode",{parentName:"li"},"y")," is the MCS rates (packet size 800B). Only have\ndone 4 hop and 5 hop."))),(0,a.kt)("li",{parentName:"ul"},"Figure H tests are run on a figure 8 with two links not associated as shown\nbelow. A stream of traffic is sent from 2A \u2194 2D , while simultaneously sending\na stream from 2F \u2194 2C.")),(0,a.kt)("p",{align:"center"},(0,a.kt)("img",{src:"/terragraph-ctf/figures/throughput_test_fig8.png",width:"800"})),(0,a.kt)("p",null,"Link to throughput chart:"),(0,a.kt)("table",null,(0,a.kt)("thead",{parentName:"table"},(0,a.kt)("tr",{parentName:"thead"},(0,a.kt)("th",{parentName:"tr",align:null},"ANT_CODE"),(0,a.kt)("th",{parentName:"tr",align:null},"DUT1 Info"),(0,a.kt)("th",{parentName:"tr",align:null},"DUT2 Info"),(0,a.kt)("th",{parentName:"tr",align:null},"laMaxMcs"))),(0,a.kt)("tbody",{parentName:"table"},(0,a.kt)("tr",{parentName:"tbody"},(0,a.kt)("td",{parentName:"tr",align:null},"TP_PKTGEN-33.12"),(0,a.kt)("td",{parentName:"tr",align:null},"PCIe Gen3"),(0,a.kt)("td",{parentName:"tr",align:null},"PCI Gen3"),(0,a.kt)("td",{parentName:"tr",align:null},"12")),(0,a.kt)("tr",{parentName:"tbody"},(0,a.kt)("td",{parentName:"tr",align:null},"TP_PKTGEN-33.9"),(0,a.kt)("td",{parentName:"tr",align:null},"PCIe Gen3"),(0,a.kt)("td",{parentName:"tr",align:null},"PCI Gen3"),(0,a.kt)("td",{parentName:"tr",align:null},"9")),(0,a.kt)("tr",{parentName:"tbody"},(0,a.kt)("td",{parentName:"tr",align:null},"TP_PKTGEN-32.11"),(0,a.kt)("td",{parentName:"tr",align:null},"PCIe Gen3"),(0,a.kt)("td",{parentName:"tr",align:null},"PCI Gen2"),(0,a.kt)("td",{parentName:"tr",align:null},"11")),(0,a.kt)("tr",{parentName:"tbody"},(0,a.kt)("td",{parentName:"tr",align:null},"TP_PKTGEN-32.9"),(0,a.kt)("td",{parentName:"tr",align:null},"PCIe Gen3"),(0,a.kt)("td",{parentName:"tr",align:null},"PCI Gen2"),(0,a.kt)("td",{parentName:"tr",align:null},"9")),(0,a.kt)("tr",{parentName:"tbody"},(0,a.kt)("td",{parentName:"tr",align:null},"TP_PKTGEN-22.11"),(0,a.kt)("td",{parentName:"tr",align:null},"PCIe Gen2"),(0,a.kt)("td",{parentName:"tr",align:null},"PCI Gen2"),(0,a.kt)("td",{parentName:"tr",align:null},"11")),(0,a.kt)("tr",{parentName:"tbody"},(0,a.kt)("td",{parentName:"tr",align:null},"TP_PKTGEN-22.9"),(0,a.kt)("td",{parentName:"tr",align:null},"PCIe Gen2"),(0,a.kt)("td",{parentName:"tr",align:null},"PCI Gen2"),(0,a.kt)("td",{parentName:"tr",align:null},"9")))))}m.isMDXComponent=!0}}]);