import {test} from 'node:test';
import assert from 'node:assert/strict';
import {activityDays,groupOrders,urgentOrders,chartMaximum} from './src/dashboard-data.js';
test('pending categories keep individual deficits without offsetting credit',()=>{
 const rows=[{client:'LENNOX',quantity:100,applied:100,pending:0,credit:50},{client:'RHEEM',quantity:100,applied:0,pending:100}];
 const groups=groupOrders(rows);
 assert.equal(groups[0].label,'RHEEM');assert.equal(groups.reduce((sum,row)=>sum+row.pending,0),100);
 assert.equal(rows[0].client,'LENNOX');
});
test('same week number in different years remains separate',()=>{
 const rows=[{client:'C',year:2026,week:43,quantity:100,applied:20,pending:80},{client:'C',year:2027,week:43,quantity:200,applied:100,pending:100}];
 assert.equal(groupOrders(rows,'week').length,2);assert.equal(groupOrders(rows)[0].quantity,300);
});
test('physical production is grouped by actual date and shift within the selected period',()=>{
 const days=activityDays([{operational_date:'2026-10-15',shift__code:'A',quantity:200},{operational_date:'2026-10-15',shift__code:'B',quantity:50},{operational_date:'2026-10-16',shift__code:'A',quantity:100},{operational_date:'2026-10-09',shift__code:'A',quantity:999}],'2026-10-16',7);
 assert.equal(days.length,7);assert.equal(days[0].date,'2026-10-10');assert.equal(days.reduce((sum,day)=>sum+day.total,0),350);
 assert.deepEqual(days[5].shifts,{A:200,B:50});assert.equal(days[0].total,0);
});
test('priorities are ordered by importance and origin week without mutating input',()=>{
 const rows=[{id:1,priority:2,year:2026,week:42,pending:100},{id:2,priority:1,year:2026,week:43,pending:20},{id:3,priority:1,year:2026,week:41,pending:10},{id:4,priority:1,year:2026,week:40,pending:0}];
 assert.deepEqual(urgentOrders(rows).map(row=>row.id),[3,2,1]);assert.equal(rows[0].id,1);
});
test('chart maximum accommodates actual values and empty periods',()=>{
 for(const actual of [0,1,3,77,501,3200])assert.ok(chartMaximum(actual)>=actual&&chartMaximum(actual)>0);
});
