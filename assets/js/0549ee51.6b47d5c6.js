"use strict";(self.webpackChunkdocusaurus=self.webpackChunkdocusaurus||[]).push([[814],{3905:(t,e,l)=>{l.d(e,{Zo:()=>u,kt:()=>d});var a=l(7294);function i(t,e,l){return e in t?Object.defineProperty(t,e,{value:l,enumerable:!0,configurable:!0,writable:!0}):t[e]=l,t}function o(t,e){var l=Object.keys(t);if(Object.getOwnPropertySymbols){var a=Object.getOwnPropertySymbols(t);e&&(a=a.filter((function(e){return Object.getOwnPropertyDescriptor(t,e).enumerable}))),l.push.apply(l,a)}return l}function n(t){for(var e=1;e<arguments.length;e++){var l=null!=arguments[e]?arguments[e]:{};e%2?o(Object(l),!0).forEach((function(e){i(t,e,l[e])})):Object.getOwnPropertyDescriptors?Object.defineProperties(t,Object.getOwnPropertyDescriptors(l)):o(Object(l)).forEach((function(e){Object.defineProperty(t,e,Object.getOwnPropertyDescriptor(l,e))}))}return t}function r(t,e){if(null==t)return{};var l,a,i=function(t,e){if(null==t)return{};var l,a,i={},o=Object.keys(t);for(a=0;a<o.length;a++)l=o[a],e.indexOf(l)>=0||(i[l]=t[l]);return i}(t,e);if(Object.getOwnPropertySymbols){var o=Object.getOwnPropertySymbols(t);for(a=0;a<o.length;a++)l=o[a],e.indexOf(l)>=0||Object.prototype.propertyIsEnumerable.call(t,l)&&(i[l]=t[l])}return i}var p=a.createContext({}),s=function(t){var e=a.useContext(p),l=e;return t&&(l="function"==typeof t?t(e):n(n({},e),t)),l},u=function(t){var e=s(t.components);return a.createElement(p.Provider,{value:e},t.children)},k={inlineCode:"code",wrapper:function(t){var e=t.children;return a.createElement(a.Fragment,{},e)}},m=a.forwardRef((function(t,e){var l=t.components,i=t.mdxType,o=t.originalType,p=t.parentName,u=r(t,["components","mdxType","originalType","parentName"]),m=s(l),d=i,c=m["".concat(p,".").concat(d)]||m[d]||k[d]||o;return l?a.createElement(c,n(n({ref:e},u),{},{components:l})):a.createElement(c,n({ref:e},u))}));function d(t,e){var l=arguments,i=e&&e.mdxType;if("string"==typeof t||i){var o=l.length,n=new Array(o);n[0]=m;var r={};for(var p in e)hasOwnProperty.call(e,p)&&(r[p]=e[p]);r.originalType=t,r.mdxType="string"==typeof t?t:i,n[1]=r;for(var s=2;s<o;s++)n[s]=l[s];return a.createElement.apply(null,n)}return a.createElement.apply(null,l)}m.displayName="MDXCreateElement"},5834:(t,e,l)=>{l.r(e),l.d(e,{assets:()=>p,contentTitle:()=>n,default:()=>k,frontMatter:()=>o,metadata:()=>r,toc:()=>s});var a=l(7462),i=(l(7294),l(3905));const o={},n="Stability Tests",r={unversionedId:"tests/Stability",id:"tests/Stability",title:"Stability Tests",description:"P2P",source:"@site/../docs/tests/Stability.md",sourceDirName:"tests",slug:"/tests/Stability",permalink:"/terragraph-ctf/tests/Stability",draft:!1,editUrl:"https://github.com/terragraph/terragraph-ctf/edit/main/docs/../docs/tests/Stability.md",tags:[],version:"current",frontMatter:{},sidebar:"docs",previous:{title:"E2E Controller Tests",permalink:"/terragraph-ctf/tests/E2E_Controller"},next:{title:"RFC 2544 Tests",permalink:"/terragraph-ctf/tests/RFC_2544"}},p={},s=[{value:"P2P",id:"p2p",level:2},{value:"<code>PUMA_RF_STA1</code> Low Load Availability - P2P",id:"puma_rf_sta1-low-load-availability---p2p",level:3},{value:"<code>PUMA_RF_STA2</code> Medium Load Availability - P2P",id:"puma_rf_sta2-medium-load-availability---p2p",level:3},{value:"<code>PUMA_RF_STA3</code> High Load Availability - P2P",id:"puma_rf_sta3-high-load-availability---p2p",level:3},{value:"<code>PUMA_RF_STA3.1</code> High Load Availability - P2P",id:"puma_rf_sta31-high-load-availability---p2p",level:3},{value:"<code>PUMA_RF_STA4</code> Burst Mode Availability - P2P",id:"puma_rf_sta4-burst-mode-availability---p2p",level:3},{value:"P2MP",id:"p2mp",level:2},{value:"<code>PUMA_RF_STA5</code> Low Load Availability - P2MP",id:"puma_rf_sta5-low-load-availability---p2mp",level:3},{value:"<code>PUMA_RF_STA6</code> Medium Load Availability - P2MP",id:"puma_rf_sta6-medium-load-availability---p2mp",level:3},{value:"<code>PUMA_RF_STA7</code> High Load Availability - P2MP",id:"puma_rf_sta7-high-load-availability---p2mp",level:3},{value:"<code>PUMA_RF_STA8</code> Burst Mode Availability - P2MP",id:"puma_rf_sta8-burst-mode-availability---p2mp",level:3},{value:"<code>PUMA_RF_STA16</code> High Load Availability - P2MP",id:"puma_rf_sta16-high-load-availability---p2mp",level:3},{value:"Multi-Hop Setup",id:"multi-hop-setup",level:2},{value:"<code>PUMA_RF_STA9</code> Low Load Availability - Fig-of-8 (Multi-Hop)",id:"puma_rf_sta9-low-load-availability---fig-of-8-multi-hop",level:3},{value:"<code>PUMA_RF_STA10</code> Medium Load Availability - Fig-of-8 (Multi-Hop)",id:"puma_rf_sta10-medium-load-availability---fig-of-8-multi-hop",level:3},{value:"<code>PUMA_RF_STA11</code> Low Load Availability of a LSN network (Fig-of-8 or larger)",id:"puma_rf_sta11-low-load-availability-of-a-lsn-network-fig-of-8-or-larger",level:3},{value:"<code>PUMA_RF_STA12</code> Medium Load Availability of a LSN network (Fig-of-8 or larger)",id:"puma_rf_sta12-medium-load-availability-of-a-lsn-network-fig-of-8-or-larger",level:3},{value:"<code>PUMA_RF_STA13</code> Low Load Availability of a LSN network with scans enabled (Fig-of-8 or larger)",id:"puma_rf_sta13-low-load-availability-of-a-lsn-network-with-scans-enabled-fig-of-8-or-larger",level:3},{value:"<code>PUMA_RF_STA14</code> High Load Availability - Fig-of-8 (Multi-Hop)",id:"puma_rf_sta14-high-load-availability---fig-of-8-multi-hop",level:3},{value:"<code>PUMA_RF_STA15</code> Low Load Availability - Fremont Puma Multi-Hop",id:"puma_rf_sta15-low-load-availability---fremont-puma-multi-hop",level:3}],u={toc:s};function k(t){let{components:e,...l}=t;return(0,i.kt)("wrapper",(0,a.Z)({},u,l,{components:e,mdxType:"MDXLayout"}),(0,i.kt)("h1",{id:"stability-tests"},"Stability Tests"),(0,i.kt)("h2",{id:"p2p"},"P2P"),(0,i.kt)("h3",{id:"puma_rf_sta1-low-load-availability---p2p"},(0,i.kt)("inlineCode",{parentName:"h3"},"PUMA_RF_STA1")," Low Load Availability - P2P"),(0,i.kt)("p",null,"Description: This test checks network availability on a P2P setup with a load of\n50Mbps."),(0,i.kt)("p",null,"Test Setup: P2P"),(0,i.kt)("p",null,"Procedure:"),(0,i.kt)("ol",null,(0,i.kt)("li",{parentName:"ol"},"On the P2P setup, ignite the network using E2E."),(0,i.kt)("li",{parentName:"ol"},"Ping over the terra interface to make sure the link is up",(0,i.kt)("ol",{parentName:"li"},(0,i.kt)("li",{parentName:"ol"},"Duration : 2 mins"),(0,i.kt)("li",{parentName:"ol"},"Interval : 0.2 s"),(0,i.kt)("li",{parentName:"ol"},"Allowed packet loss : 10%"))),(0,i.kt)("li",{parentName:"ol"},"Ping over the CPE interface to make sure the end-to-end connection is up",(0,i.kt)("ol",{parentName:"li"},(0,i.kt)("li",{parentName:"ol"},"Duration : 2 mins"),(0,i.kt)("li",{parentName:"ol"},"Interval : 0.2 s"),(0,i.kt)("li",{parentName:"ol"},"Allowed packet loss : 40%"))),(0,i.kt)("li",{parentName:"ol"},"Run iPerf between two nodes with the following characteristics:",(0,i.kt)("ol",{parentName:"li"},(0,i.kt)("li",{parentName:"ol"},"50Mbps"),(0,i.kt)("li",{parentName:"ol"},"UDP/Bidirectional"),(0,i.kt)("li",{parentName:"ol"},"Duration of 8 hours minimum")))),(0,i.kt)("p",null,"Pass/Fail Criteria:"),(0,i.kt)("ol",null,(0,i.kt)("li",{parentName:"ol"},"Link must be available for all 8 hours")),(0,i.kt)("h3",{id:"puma_rf_sta2-medium-load-availability---p2p"},(0,i.kt)("inlineCode",{parentName:"h3"},"PUMA_RF_STA2")," Medium Load Availability - P2P"),(0,i.kt)("p",null,"Description: This test checks network availability on a P2P setup with a load of\n950 Mbps."),(0,i.kt)("p",null,"Test Setup: P2P"),(0,i.kt)("p",null,"Procedure:"),(0,i.kt)("ol",null,(0,i.kt)("li",{parentName:"ol"},"On the P2P setup, ignite the network using E2E."),(0,i.kt)("li",{parentName:"ol"},"Ping over the terra interface to make sure the link is up",(0,i.kt)("ol",{parentName:"li"},(0,i.kt)("li",{parentName:"ol"},"Duration : 2 mins"),(0,i.kt)("li",{parentName:"ol"},"Interval : 0.2 s"),(0,i.kt)("li",{parentName:"ol"},"Allowed packet loss : 10%"))),(0,i.kt)("li",{parentName:"ol"},"Ping over the CPE interface to make sure the end-to-end connection is up",(0,i.kt)("ol",{parentName:"li"},(0,i.kt)("li",{parentName:"ol"},"Duration : 2 mins"),(0,i.kt)("li",{parentName:"ol"},"Interval : 0.2 s"),(0,i.kt)("li",{parentName:"ol"},"Allowed packet loss : 40%"))),(0,i.kt)("li",{parentName:"ol"},"Run iPerf between DN to CN with the following characteristics:",(0,i.kt)("ol",{parentName:"li"},(0,i.kt)("li",{parentName:"ol"},"950 Mbps"),(0,i.kt)("li",{parentName:"ol"},"UDP/Bidirectional"),(0,i.kt)("li",{parentName:"ol"},"Duration of 8 hours minimum")))),(0,i.kt)("p",null,"Pass/Fail Criteria:"),(0,i.kt)("ol",null,(0,i.kt)("li",{parentName:"ol"},"Availability should be 99.9%")),(0,i.kt)("h3",{id:"puma_rf_sta3-high-load-availability---p2p"},(0,i.kt)("inlineCode",{parentName:"h3"},"PUMA_RF_STA3")," High Load Availability - P2P"),(0,i.kt)("p",null,"Description: This test checks network availability on a P2P setup with a load of\n1.2Gbps."),(0,i.kt)("p",null,"Test Setup: P2P"),(0,i.kt)("p",null,"Procedure:"),(0,i.kt)("ol",null,(0,i.kt)("li",{parentName:"ol"},"On the P2P setup, ignite the network using E2E."),(0,i.kt)("li",{parentName:"ol"},"Ping over the terra interface to make sure the link is up",(0,i.kt)("ol",{parentName:"li"},(0,i.kt)("li",{parentName:"ol"},"Duration : 2 mins"),(0,i.kt)("li",{parentName:"ol"},"Interval : 0.2 s"),(0,i.kt)("li",{parentName:"ol"},"Allowed packet loss : 10%"))),(0,i.kt)("li",{parentName:"ol"},"Ping over the CPE interface to make sure the end-to-end connection is up",(0,i.kt)("ol",{parentName:"li"},(0,i.kt)("li",{parentName:"ol"},"Duration : 2 mins"),(0,i.kt)("li",{parentName:"ol"},"Interval : 0.2 s"),(0,i.kt)("li",{parentName:"ol"},"Allowed packet loss : 40%"))),(0,i.kt)("li",{parentName:"ol"},"Run iPerf between DN to CN with the following characteristics:",(0,i.kt)("ol",{parentName:"li"},(0,i.kt)("li",{parentName:"ol"},"1.2 Gbps"),(0,i.kt)("li",{parentName:"ol"},"UDP/Bidirectional"),(0,i.kt)("li",{parentName:"ol"},"Duration of 8 hours minimum")))),(0,i.kt)("p",null,"Pass/Fail Criteria:"),(0,i.kt)("ol",null,(0,i.kt)("li",{parentName:"ol"},"Availability should be 99.9%")),(0,i.kt)("h3",{id:"puma_rf_sta31-high-load-availability---p2p"},(0,i.kt)("inlineCode",{parentName:"h3"},"PUMA_RF_STA3.1")," High Load Availability - P2P"),(0,i.kt)("p",null,"Description: This test checks network availability on a P2P setup with a load of\n2Gbps."),(0,i.kt)("p",null,"Test Setup: P2P"),(0,i.kt)("p",null,"Procedure:"),(0,i.kt)("ol",null,(0,i.kt)("li",{parentName:"ol"},"On the P2P setup, ignite the network using E2E."),(0,i.kt)("li",{parentName:"ol"},"Ping over the terra interface to make sure the link is up",(0,i.kt)("ol",{parentName:"li"},(0,i.kt)("li",{parentName:"ol"},"Duration : 2 mins"),(0,i.kt)("li",{parentName:"ol"},"Interval : 0.2 s"),(0,i.kt)("li",{parentName:"ol"},"Allowed packet loss : 10%"))),(0,i.kt)("li",{parentName:"ol"},"Ping over the CPE interface to make sure the end-to-end connection is up",(0,i.kt)("ol",{parentName:"li"},(0,i.kt)("li",{parentName:"ol"},"Duration : 2 mins"),(0,i.kt)("li",{parentName:"ol"},"Interval : 0.2 s"),(0,i.kt)("li",{parentName:"ol"},"Allowed packet loss : 40%"))),(0,i.kt)("li",{parentName:"ol"},"Run iPerf between DN to CN with the following characteristics:",(0,i.kt)("ol",{parentName:"li"},(0,i.kt)("li",{parentName:"ol"},"2 Gbps"),(0,i.kt)("li",{parentName:"ol"},"UDP/Bidirectional"),(0,i.kt)("li",{parentName:"ol"},"Duration of 8 hours minimum")))),(0,i.kt)("p",null,"Pass/Fail Criteria:"),(0,i.kt)("ol",null,(0,i.kt)("li",{parentName:"ol"},"Availability should be 99.9%")),(0,i.kt)("h3",{id:"puma_rf_sta4-burst-mode-availability---p2p"},(0,i.kt)("inlineCode",{parentName:"h3"},"PUMA_RF_STA4")," Burst Mode Availability - P2P"),(0,i.kt)("p",null,"Description: This test checks network availability on a P2P setup with a burst\nload of 1.5 Gbps."),(0,i.kt)("p",null,"Test Setup: P2P"),(0,i.kt)("p",null,"Procedure:"),(0,i.kt)("ol",null,(0,i.kt)("li",{parentName:"ol"},"On the P2P setup, ignite the network using E2E."),(0,i.kt)("li",{parentName:"ol"},"Ping over the terra interface to make sure the link is up",(0,i.kt)("ol",{parentName:"li"},(0,i.kt)("li",{parentName:"ol"},"Duration : 2 mins"),(0,i.kt)("li",{parentName:"ol"},"Interval : 0.2 s"),(0,i.kt)("li",{parentName:"ol"},"Allowed packet loss : 10%"))),(0,i.kt)("li",{parentName:"ol"},"Ping over the CPE interface to make sure the end-to-end connection is up",(0,i.kt)("ol",{parentName:"li"},(0,i.kt)("li",{parentName:"ol"},"Duration : 2 mins"),(0,i.kt)("li",{parentName:"ol"},"Interval : 0.2 s"),(0,i.kt)("li",{parentName:"ol"},"Allowed packet loss : 40%"))),(0,i.kt)("li",{parentName:"ol"},"Run iPerf between DN to CN with the following characteristics:",(0,i.kt)("ol",{parentName:"li"},(0,i.kt)("li",{parentName:"ol"},"1000 Mbps"),(0,i.kt)("li",{parentName:"ol"},"UDP/Bidirectional"),(0,i.kt)("li",{parentName:"ol"},"Duration of 8 hours minimum"),(0,i.kt)("li",{parentName:"ol"},"In parallel, after every 1 hour, send iPerf of 3Gbps UDP, bidirectional\nfor 15 minutes.")))),(0,i.kt)("p",null,"Pass/Fail Criteria:"),(0,i.kt)("ol",null,(0,i.kt)("li",{parentName:"ol"},"Availability should be 99.9%"),(0,i.kt)("li",{parentName:"ol"},"Every link must get 1000Mbps all the time")),(0,i.kt)("h2",{id:"p2mp"},"P2MP"),(0,i.kt)("h3",{id:"puma_rf_sta5-low-load-availability---p2mp"},(0,i.kt)("inlineCode",{parentName:"h3"},"PUMA_RF_STA5")," Low Load Availability - P2MP"),(0,i.kt)("p",null,"Description: This test checks network availability on a P2MP setup with a load\nof 50Mbps."),(0,i.kt)("p",null,"Test Setup: P2MP"),(0,i.kt)("p",null,"Procedure:"),(0,i.kt)("ol",null,(0,i.kt)("li",{parentName:"ol"},"On the P2MP setup, ignite the network using E2E."),(0,i.kt)("li",{parentName:"ol"},"Ping over the terra interface to make sure the link is up",(0,i.kt)("ol",{parentName:"li"},(0,i.kt)("li",{parentName:"ol"},"Duration : 2 mins"),(0,i.kt)("li",{parentName:"ol"},"Interval : 0.2 s"),(0,i.kt)("li",{parentName:"ol"},"Allowed packet loss : 10%"))),(0,i.kt)("li",{parentName:"ol"},"Ping over the CPE interface to make sure the end-to-end connection is up",(0,i.kt)("ol",{parentName:"li"},(0,i.kt)("li",{parentName:"ol"},"Duration : 2 mins"),(0,i.kt)("li",{parentName:"ol"},"Interval : 0.2 s"),(0,i.kt)("li",{parentName:"ol"},"Allowed packet loss : 40%"))),(0,i.kt)("li",{parentName:"ol"},"Run iPerf between initiator to 7 responder nodes with the following\ncharacteristics:",(0,i.kt)("ol",{parentName:"li"},(0,i.kt)("li",{parentName:"ol"},"50Mbps"),(0,i.kt)("li",{parentName:"ol"},"UDP/Bidirectional"),(0,i.kt)("li",{parentName:"ol"},"Duration of 8 hours minimum")))),(0,i.kt)("p",null,"Pass/Fail Criteria:"),(0,i.kt)("ol",null,(0,i.kt)("li",{parentName:"ol"},"Availability should be 99.9%")),(0,i.kt)("h3",{id:"puma_rf_sta6-medium-load-availability---p2mp"},(0,i.kt)("inlineCode",{parentName:"h3"},"PUMA_RF_STA6")," Medium Load Availability - P2MP"),(0,i.kt)("p",null,"Description: This test checks network availability on a P2MP setup with a load\nof 950 Mbps."),(0,i.kt)("p",null,"Test Setup: P2MP"),(0,i.kt)("p",null,"Procedure:"),(0,i.kt)("ol",null,(0,i.kt)("li",{parentName:"ol"},"On the P2MP setup, ignite the network using E2E."),(0,i.kt)("li",{parentName:"ol"},"Ping over the terra interface to make sure the link is up",(0,i.kt)("ol",{parentName:"li"},(0,i.kt)("li",{parentName:"ol"},"Duration : 2 mins"),(0,i.kt)("li",{parentName:"ol"},"Interval : 0.2 s"),(0,i.kt)("li",{parentName:"ol"},"Allowed packet loss : 10%"))),(0,i.kt)("li",{parentName:"ol"},"Ping over the CPE interface to make sure the end-to-end connection is up",(0,i.kt)("ol",{parentName:"li"},(0,i.kt)("li",{parentName:"ol"},"Duration : 2 mins"),(0,i.kt)("li",{parentName:"ol"},"Interval : 0.2 s"),(0,i.kt)("li",{parentName:"ol"},"Allowed packet loss : 40%"))),(0,i.kt)("li",{parentName:"ol"},"Run iPerf between initiator to 7 responder nodes with the following\ncharacteristics:",(0,i.kt)("ol",{parentName:"li"},(0,i.kt)("li",{parentName:"ol"},"950 Mbps"),(0,i.kt)("li",{parentName:"ol"},"UDP/Bidirectional"),(0,i.kt)("li",{parentName:"ol"},"Duration of 8 hours minimum")))),(0,i.kt)("p",null,"Pass/Fail Criteria:"),(0,i.kt)("ol",null,(0,i.kt)("li",{parentName:"ol"},"Availability should be 99.9%")),(0,i.kt)("h3",{id:"puma_rf_sta7-high-load-availability---p2mp"},(0,i.kt)("inlineCode",{parentName:"h3"},"PUMA_RF_STA7")," High Load Availability - P2MP"),(0,i.kt)("p",null,"Description: This test checks network availability on a P2MP setup with a load\nof 1.2Gbps."),(0,i.kt)("p",null,"Test Setup: P2MP"),(0,i.kt)("p",null,"Procedure:"),(0,i.kt)("ol",null,(0,i.kt)("li",{parentName:"ol"},"On the P2MP setup, ignite the network using E2E."),(0,i.kt)("li",{parentName:"ol"},"Ping over the terra interface to make sure the link is up",(0,i.kt)("ol",{parentName:"li"},(0,i.kt)("li",{parentName:"ol"},"Duration : 2 mins"),(0,i.kt)("li",{parentName:"ol"},"Interval : 0.2 s"),(0,i.kt)("li",{parentName:"ol"},"Allowed packet loss : 10%"))),(0,i.kt)("li",{parentName:"ol"},"Ping over the CPE interface to make sure the end-to-end connection is up",(0,i.kt)("ol",{parentName:"li"},(0,i.kt)("li",{parentName:"ol"},"Duration : 2 mins"),(0,i.kt)("li",{parentName:"ol"},"Interval : 0.2 s"),(0,i.kt)("li",{parentName:"ol"},"Allowed packet loss : 40%"))),(0,i.kt)("li",{parentName:"ol"},"Run iPerf between initiator to 7 responder nodes with the following\ncharacteristics:",(0,i.kt)("ol",{parentName:"li"},(0,i.kt)("li",{parentName:"ol"},"1.2 Gbps"),(0,i.kt)("li",{parentName:"ol"},"UDP/Bidirectional"),(0,i.kt)("li",{parentName:"ol"},"Duration of 8 hours minimum")))),(0,i.kt)("p",null,"Pass/Fail Criteria:"),(0,i.kt)("ol",null,(0,i.kt)("li",{parentName:"ol"},"Availability should be 99.9%")),(0,i.kt)("h3",{id:"puma_rf_sta8-burst-mode-availability---p2mp"},(0,i.kt)("inlineCode",{parentName:"h3"},"PUMA_RF_STA8")," Burst Mode Availability - P2MP"),(0,i.kt)("p",null,"Description: This test checks network availability on a P2MP setup with a burst\nload of 1 Gbps."),(0,i.kt)("p",null,"Test Setup: P2MP"),(0,i.kt)("p",null,"Procedure:"),(0,i.kt)("ol",null,(0,i.kt)("li",{parentName:"ol"},"On the P2MP setup, ignite the network using E2E."),(0,i.kt)("li",{parentName:"ol"},"Ping over the terra interface to make sure the link is up",(0,i.kt)("ol",{parentName:"li"},(0,i.kt)("li",{parentName:"ol"},"Duration : 2 mins"),(0,i.kt)("li",{parentName:"ol"},"Interval : 0.2 s"),(0,i.kt)("li",{parentName:"ol"},"Allowed packet loss : 10%"))),(0,i.kt)("li",{parentName:"ol"},"Ping over the CPE interface to make sure the end-to-end connection is up",(0,i.kt)("ol",{parentName:"li"},(0,i.kt)("li",{parentName:"ol"},"Duration : 2 mins"),(0,i.kt)("li",{parentName:"ol"},"Interval : 0.2 s"),(0,i.kt)("li",{parentName:"ol"},"Allowed packet loss : 40%"))),(0,i.kt)("li",{parentName:"ol"},"Run iPerf between initiator to 7 responder nodes with the following\ncharacteristics:",(0,i.kt)("ol",{parentName:"li"},(0,i.kt)("li",{parentName:"ol"},"1000 Mbps"),(0,i.kt)("li",{parentName:"ol"},"UDP/Bidirectional"),(0,i.kt)("li",{parentName:"ol"},"Duration of 8 hours minimum"),(0,i.kt)("li",{parentName:"ol"},"In parallel, after every 1 hour, send iPerf of 3Gbps UDP, bidirectional\nfor 15 minutes.")))),(0,i.kt)("p",null,"Pass/Fail Criteria:"),(0,i.kt)("ol",null,(0,i.kt)("li",{parentName:"ol"},"Availability should be 99.9%"),(0,i.kt)("li",{parentName:"ol"},"DN link must get 1000Mbps all the time")),(0,i.kt)("h3",{id:"puma_rf_sta16-high-load-availability---p2mp"},(0,i.kt)("inlineCode",{parentName:"h3"},"PUMA_RF_STA16")," High Load Availability - P2MP"),(0,i.kt)("p",null,"Description: This test checks network availability on a P2MP setup with a load\nof 1.2Gbps."),(0,i.kt)("p",null,"Test Setup: P2MP"),(0,i.kt)("p",null,"Procedure:"),(0,i.kt)("ol",null,(0,i.kt)("li",{parentName:"ol"},"On the P2MP setup, ignite the network using E2E."),(0,i.kt)("li",{parentName:"ol"},"Ping over the terra interface to make sure the link is up",(0,i.kt)("ol",{parentName:"li"},(0,i.kt)("li",{parentName:"ol"},"Duration : 2 mins"),(0,i.kt)("li",{parentName:"ol"},"Interval : 0.2 s"),(0,i.kt)("li",{parentName:"ol"},"Allowed packet loss : 10%"))),(0,i.kt)("li",{parentName:"ol"},"Ping over the CPE interface to make sure the end-to-end connection is up",(0,i.kt)("ol",{parentName:"li"},(0,i.kt)("li",{parentName:"ol"},"Duration : 2 mins"),(0,i.kt)("li",{parentName:"ol"},"Interval : 0.2 s"),(0,i.kt)("li",{parentName:"ol"},"Allowed packet loss : 40%"))),(0,i.kt)("li",{parentName:"ol"},"Run iPerf between initiator to 8 responder nodes with the following\ncharacteristics:",(0,i.kt)("ol",{parentName:"li"},(0,i.kt)("li",{parentName:"ol"},"1.2 Gbps"),(0,i.kt)("li",{parentName:"ol"},"UDP/Bidirectional"),(0,i.kt)("li",{parentName:"ol"},"Duration of 8 hours minimum")))),(0,i.kt)("p",null,"Pass/Fail Criteria:"),(0,i.kt)("ol",null,(0,i.kt)("li",{parentName:"ol"},"Availability should be 99.9%")),(0,i.kt)("h2",{id:"multi-hop-setup"},"Multi-Hop Setup"),(0,i.kt)("h3",{id:"puma_rf_sta9-low-load-availability---fig-of-8-multi-hop"},(0,i.kt)("inlineCode",{parentName:"h3"},"PUMA_RF_STA9")," Low Load Availability - Fig-of-8 (Multi-Hop)"),(0,i.kt)("p",null,"Description: This test checks network availability on a fig-of-8 setup with a\nload of 50Mbps."),(0,i.kt)("p",null,"Test Setup: fig-of-8"),(0,i.kt)("p",null,"Procedure:"),(0,i.kt)("ol",null,(0,i.kt)("li",{parentName:"ol"},"Bring up the fig-of-8 network using E2E controller."),(0,i.kt)("li",{parentName:"ol"},"Run iPerf between POP nodes to all nodes with the following characteristics:",(0,i.kt)("ol",{parentName:"li"},(0,i.kt)("li",{parentName:"ol"},"50Mbps (Note: POP links might be hitting capacity)"),(0,i.kt)("li",{parentName:"ol"},"UDP/Bidirectional"),(0,i.kt)("li",{parentName:"ol"},"Duration of 24 hours and for 3 days.")))),(0,i.kt)("p",null,"Pass/Fail Criteria:"),(0,i.kt)("ol",null,(0,i.kt)("li",{parentName:"ol"},"Availability should be 99.9%")),(0,i.kt)("p",null,"Note: Need to add tests on measuring availability metrics."),(0,i.kt)("h3",{id:"puma_rf_sta10-medium-load-availability---fig-of-8-multi-hop"},(0,i.kt)("inlineCode",{parentName:"h3"},"PUMA_RF_STA10")," Medium Load Availability - Fig-of-8 (Multi-Hop)"),(0,i.kt)("p",null,"Description: This test checks network availability on a fig-of-8 setup with a\nload of 100 Mbps."),(0,i.kt)("p",null,"Test Setup: fig-of-8"),(0,i.kt)("p",null,"Procedure:"),(0,i.kt)("ol",null,(0,i.kt)("li",{parentName:"ol"},"Bring up the fig-of-8 network using E2E controller."),(0,i.kt)("li",{parentName:"ol"},"Run iPerf between POP nodes to all nodes with the following characteristics:",(0,i.kt)("ol",{parentName:"li"},(0,i.kt)("li",{parentName:"ol"},"100Mbps (Note: POP links might be hitting capacity)"),(0,i.kt)("li",{parentName:"ol"},"UDP/Bidirectional"),(0,i.kt)("li",{parentName:"ol"},"Duration of 24 hours and for 4 days.")))),(0,i.kt)("p",null,"Pass/Fail Criteria:"),(0,i.kt)("ol",null,(0,i.kt)("li",{parentName:"ol"},"Availability should be 99.9%")),(0,i.kt)("p",null,"Note: Need to add tests on measuring availability metrics."),(0,i.kt)("h3",{id:"puma_rf_sta11-low-load-availability-of-a-lsn-network-fig-of-8-or-larger"},(0,i.kt)("inlineCode",{parentName:"h3"},"PUMA_RF_STA11")," Low Load Availability of a LSN network (Fig-of-8 or larger)"),(0,i.kt)("p",null,"Description: This test checks network availability on a RF fig-of-8 (or larger)\nsetup with a load of 50Mbps."),(0,i.kt)("p",null,"Test Setup: RF fig-of-8 (preferably larger)"),(0,i.kt)("p",null,"Procedure:"),(0,i.kt)("ol",null,(0,i.kt)("li",{parentName:"ol"},"Bring up the network using E2E controller."),(0,i.kt)("li",{parentName:"ol"},"Run iPerf between POP nodes to all nodes with the following characteristics:",(0,i.kt)("ol",{parentName:"li"},(0,i.kt)("li",{parentName:"ol"},"50Mbps (Note: POP links might be hitting capacity)"),(0,i.kt)("li",{parentName:"ol"},"UDP/Bidirectional"),(0,i.kt)("li",{parentName:"ol"},"Duration of 24 hours and for 3 days.")))),(0,i.kt)("p",null,"Pass/Fail Criteria:"),(0,i.kt)("ol",null,(0,i.kt)("li",{parentName:"ol"},"Availability should be 99.9%")),(0,i.kt)("h3",{id:"puma_rf_sta12-medium-load-availability-of-a-lsn-network-fig-of-8-or-larger"},(0,i.kt)("inlineCode",{parentName:"h3"},"PUMA_RF_STA12")," Medium Load Availability of a LSN network (Fig-of-8 or larger)"),(0,i.kt)("p",null,"Description: This test checks network availability on a RF fig-of-8 (or larger)\nsetup with a load of 50Mbps."),(0,i.kt)("p",null,"Test Setup: RF fig-of-8 (preferably larger)"),(0,i.kt)("p",null,"Procedure:"),(0,i.kt)("ol",null,(0,i.kt)("li",{parentName:"ol"},"Bring up the network using E2E controller."),(0,i.kt)("li",{parentName:"ol"},"Run iPerf between  POP nodes to all nodes with the following characteristics:",(0,i.kt)("ol",{parentName:"li"},(0,i.kt)("li",{parentName:"ol"},"100Mbps (Note: POP links might be hitting capacity)"),(0,i.kt)("li",{parentName:"ol"},"UDP/Bidirectional"),(0,i.kt)("li",{parentName:"ol"},"Duration of 24 hours and for 4 days.")))),(0,i.kt)("p",null,"Pass/Fail Criteria:"),(0,i.kt)("ol",null,(0,i.kt)("li",{parentName:"ol"},"Availability should be 99.9%")),(0,i.kt)("h3",{id:"puma_rf_sta13-low-load-availability-of-a-lsn-network-with-scans-enabled-fig-of-8-or-larger"},(0,i.kt)("inlineCode",{parentName:"h3"},"PUMA_RF_STA13")," Low Load Availability of a LSN network with scans enabled (Fig-of-8 or larger)"),(0,i.kt)("p",null,"Test Setup: Figure-8 (RF) (preferably with P2MP)"),(0,i.kt)("p",null,"Procedure:"),(0,i.kt)("ul",null,(0,i.kt)("li",{parentName:"ul"},"Bring up network and run 50Mbps traffic from POP node to every node in the\nnetwork"),(0,i.kt)("li",{parentName:"ul"},"Enable periodic scans (PBF & IM) through E2E scan APIs"),(0,i.kt)("li",{parentName:"ul"},"Run scans for 24 hours"),(0,i.kt)("li",{parentName:"ul"},(0,i.kt)("strong",{parentName:"li"},"Note:")," should be run after basic network stability test (",(0,i.kt)("inlineCode",{parentName:"li"},"PUMA_RF_STA11"),")")),(0,i.kt)("p",null,"Pass/Fail Criteria:"),(0,i.kt)("ul",null,(0,i.kt)("li",{parentName:"ul"},"Confirm periodic scans are running from scan schedule"),(0,i.kt)("li",{parentName:"ul"},"Network availability should be greater than 99.9%")),(0,i.kt)("h3",{id:"puma_rf_sta14-high-load-availability---fig-of-8-multi-hop"},(0,i.kt)("inlineCode",{parentName:"h3"},"PUMA_RF_STA14")," High Load Availability - Fig-of-8 (Multi-Hop)"),(0,i.kt)("p",null,"Description: This test checks network availability on a fig-of-8 setup with a\nload of 1000Mbps."),(0,i.kt)("p",null,"Test Setup: fig-of-8"),(0,i.kt)("p",null,"Procedure:"),(0,i.kt)("ol",null,(0,i.kt)("li",{parentName:"ol"},"Bring up the fig-of-8 network."),(0,i.kt)("li",{parentName:"ol"},"Run iPerf from POP node to another node (5Hop) with the following\ncharacteristics:",(0,i.kt)("ol",{parentName:"li"},(0,i.kt)("li",{parentName:"ol"},"1000Mbps"),(0,i.kt)("li",{parentName:"ol"},"UDP/Bidirectional"),(0,i.kt)("li",{parentName:"ol"},"Duration of 8 hours")))),(0,i.kt)("p",null,"Pass/Fail Criteria:"),(0,i.kt)("ol",null,(0,i.kt)("li",{parentName:"ol"},"Availability should be 99.9%")),(0,i.kt)("h3",{id:"puma_rf_sta15-low-load-availability---fremont-puma-multi-hop"},(0,i.kt)("inlineCode",{parentName:"h3"},"PUMA_RF_STA15")," Low Load Availability - Fremont Puma Multi-Hop"),(0,i.kt)("p",null,"Description: This test checks network availability on a Fremont Puma Multi-Hop\nsetup with a load of 50Mbps."),(0,i.kt)("p",null,"Test Setup: Fremont Puma Multi-Hop"),(0,i.kt)("p",null,"Procedure:"),(0,i.kt)("ol",null,(0,i.kt)("li",{parentName:"ol"},"Bring up the network."),(0,i.kt)("li",{parentName:"ol"},"Run iPerf between POP nodes to all nodes with the following characteristics:",(0,i.kt)("ol",{parentName:"li"},(0,i.kt)("li",{parentName:"ol"},"50Mbps"),(0,i.kt)("li",{parentName:"ol"},"UDP/Bidirectional"),(0,i.kt)("li",{parentName:"ol"},"Duration of 8 hours")))),(0,i.kt)("p",null,"Pass/Fail Criteria:"),(0,i.kt)("ol",null,(0,i.kt)("li",{parentName:"ol"},"Availability should be 99.9%")))}k.isMDXComponent=!0}}]);