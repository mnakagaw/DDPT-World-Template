export function censusAge(year,asOfYear){
  return Number.isInteger(year)&&Number.isInteger(asOfYear)?Math.max(0,asOfYear-year):null;
}

export function censusRecencyClass(year,asOfYear){
  const age=censusAge(year,asOfYear);
  if(age===null)return 'unknown';
  if(age>=10)return 'overdue';
  if(age>6)return 'aging';
  if(age>3)return 'recent';
  return 'current';
}

export function censusRecencyColor(year,asOfYear){
  return {current:'#155e4b',recent:'#4c987a',aging:'#a8cfba',overdue:'#e8aaa5',unknown:'#d8dee1'}[censusRecencyClass(year,asOfYear)];
}

export function censusIntervals(rounds){
  const years=(Array.isArray(rounds)?rounds:[]).map(round=>Number(round.year)).filter(Number.isInteger);
  return years.slice(0,-1).map((year,index)=>year-years[index+1]);
}
