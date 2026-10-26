"""Human keyboard bridge: preserve brief movement taps across policy boundaries."""
class BufferedKeys:
    def __init__(self, movement, min_updates=3):
        self.movement=set(movement);self.minimum=min_updates
        self.frame=0;self.pressed={};self.pending={}
    def update(self,events,force_release=False):
        self.frame+=1;out=[]
        if force_release:
            out=[('release',key) for key in self.pressed]
            self.pressed.clear();self.pending.clear()
            return out
        for kind,key in events:
            if kind=='press':
                self.pending.pop(key,None)
                if key not in self.pressed:
                    self.pressed[key]=self.frame;out.append((kind,key))
            elif key in self.pressed:
                deadline=self.pressed[key]+self.minimum
                if key in self.movement and self.frame<deadline:self.pending[key]=deadline
                else:
                    self.pressed.pop(key);self.pending.pop(key,None);out.append((kind,key))
        for key,deadline in list(self.pending.items()):
            if self.frame>=deadline:
                self.pressed.pop(key,None);self.pending.pop(key);out.append(('release',key))
        return out
