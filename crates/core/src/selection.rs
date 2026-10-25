use crate::{invalid, Error, Result};
use serde::{Deserialize, Serialize};

#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct Interval {pub start_ns:i64,pub end_ns:i64}

#[derive(Clone, Debug, Default, Serialize, Deserialize)]
pub struct IntervalSet {intervals:Vec<Interval>}
impl IntervalSet {
    pub fn new(mut intervals:Vec<Interval>) -> Result<Self> {
        if intervals.iter().any(|v|v.start_ns>=v.end_ns) {return Err(invalid("intervals must be nonempty [start,end)"));}
        intervals.sort_unstable_by_key(|v|v.start_ns);
        let mut merged:Vec<Interval>=Vec::new();
        for interval in intervals {
            if let Some(last)=merged.last_mut() {
                if interval.start_ns<=last.end_ns {last.end_ns=last.end_ns.max(interval.end_ns);continue;}
            }
            merged.push(interval);
        }
        Ok(Self {intervals:merged})
    }
    pub fn intervals(&self)->&[Interval] {&self.intervals}
    pub fn contains(&self,t:i64)->bool {
        let i=self.intervals.partition_point(|v|v.start_ns<=t);
        i>0 && t<self.intervals[i-1].end_ns
    }
    pub fn mask(&self,times:&[i64])->Vec<bool> {times.iter().map(|&t|self.contains(t)).collect()}
    pub fn intersection(&self,other:&Self)->Self {
        let (mut i,mut j)=(0,0);let mut result=Vec::new();
        while i<self.intervals.len() && j<other.intervals.len() {
            let a=self.intervals[i];let b=other.intervals[j];
            let (start_ns,end_ns)=(a.start_ns.max(b.start_ns),a.end_ns.min(b.end_ns));
            if start_ns<end_ns {result.push(Interval{start_ns,end_ns});}
            if a.end_ns<b.end_ns {i+=1;} else {j+=1;}
        }
        Self{intervals:result}
    }
    pub fn difference(&self,other:&Self)->Self {
        let mut result=Vec::new();
        for a in &self.intervals {
            let mut cursor=a.start_ns;
            for b in other.intervals.iter().skip_while(|b|b.end_ns<=a.start_ns).take_while(|b|b.start_ns<a.end_ns) {
                if cursor<b.start_ns {result.push(Interval{start_ns:cursor,end_ns:b.start_ns});}
                cursor=cursor.max(b.end_ns);
                if cursor>=a.end_ns {break;}
            }
            if cursor<a.end_ns {result.push(Interval{start_ns:cursor,end_ns:a.end_ns});}
        }
        Self{intervals:result}
    }
    /// Expand bad intervals to all target centers whose context overlaps them.
    pub fn affected_centers(&self,history_ns:i64,future_ns:i64)->Result<Self> {
        if history_ns<0 || future_ns<0 {return Err(invalid("context lengths must be nonnegative"));}
        Self::new(self.intervals.iter().map(|v|Ok(Interval{
            start_ns:v.start_ns.checked_sub(future_ns).ok_or(Error::Overflow)?,
            end_ns:v.end_ns.checked_add(history_ns).ok_or(Error::Overflow)?,
        })).collect::<Result<Vec<_>>>()?)
    }
}
