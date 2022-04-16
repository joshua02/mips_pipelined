
# Created by Joshua Wilkinson for CS286 at SIUE

from pydoc import doc
import sys
import struct

# open files provided by the command line
infile = open(sys.argv[1], 'rb')
output = open(sys.argv[2] + "_sim.txt", 'w')
output_dis = open(sys.argv[2] + "_dis.txt", 'w')

data = infile.read()


# create an array to serve as the stack
memory = [0] * 500
instruction_as_text = [None] * 500

addr = 96


class Buffer:
    def __init__(self, length):
        self.length = length
        self.data = [None] * length
        self.elements = 0
    def push(self, value):
        for i in range(0, self.length):
            if self.data[i] == None:
                self.data[i] = value
                self.elements += 1
                return 1
        return 0
    def pop(self):
        for i in range(0, self.length-1):
            self.data[i] = self.data[i+1]
        self.data[self.length-1] = None
        self.elements -= 1

    def popEntry(self, entry):
        if entry == self.length-1:
            self.data[self.length-1] = None
        else:
            for i in range(entry, self.length-1):
                self.data[i] = self.data[i+1]
        self.data[self.length-1] = None
        self.elements -= 1
    
    def display(self):
        s = ""
        for i in range(0, self.length):
            if self.data[i] == None:
                s += "None\t"
            else:
                s += str(self.data[i]) + "\t"
        print(s)
    def getData(self, index = 0):
        return self.data[index]
    def getElements(self):
        return self.elements
    def writeDataToFile(self, output):
        for i in range(0, self.length):
            output.write("\tEntry " + str(i) + ":\t")
            if self.getData(i) != None:
                output.write("[" + self.getData(i).asText + "]")
            output.write("\n")
    def checkDestinations(self, value, maxIndex):
        for i in range(0, maxIndex):
            
            if self.getData(i) == None:
                #output.write("\nNO ENTRY ON " + str(i))
                continue
            #output.write("\n\t\t" + self.getData(i).asText + "\t\tdestination: " +str(self.getData(i).destination) + "\n")
            if self.getData(i).destination == value:
                #output.write("ENTRY ON")
                return True

        return False
    def checkReads(self, value):
        for i in range(0, self.length-1):
            if self.getData(i) == None:
                continue
            if self.getData(i).src1 == value:
                return True
            if self.getData(i).src2 == value:
                return True
        return False

        

preissue = Buffer(4)
prealu = Buffer(2)
premem = Buffer(2)
postalu = Buffer(1)
postmem = Buffer(1)
registers = [0] * 32


# function from:
# https://stackoverflow.com/questions/1604464/twos-complement-in-python
def twos_comp(val, bits):
    if (val & (1 << (bits - 1))) != 0: # if sign bit is set e.g., 8bit: 128-255
        val = val - (1 << bits)        # compute negative value
    return val 



class Instruction:
    def __init__(self, y, mem):
        self.valid = y >> 31
        self.opcode = y >> 26
        self.rs = (y >> 21) & 0x0000001F
        self.rt = (y >> 16) & 0x0000001F
        self.rd = (y >> 11) & 0x0000001F
        self.sa = (y >> 6)  & 0x0000001F
        self.instru_index = (y) & 0x03FFFFFF
        self.offset = y & 0x0000FFFF
        self.readable = ""
        self.asText = ""
        self.y = y

        self.src1 = -1
        self.src2 = -1 # register numbers
        self.destination = -1

        self.type = ""
        self.result = -1

        if self.valid == 0:
            self.asText = ('Invalid Instruction')
        elif self.opcode == 40:

            if (self.offset >> 15) == 1:
                # negative number
                self.offset = twos_comp(self.offset, 16)
            

            self.asText = ( 'ADDI\t R{0}, R{1}, #{2}'.format( self.rt, self.rs, self.offset ) )
            self.readable = 'ADDI'
            self.destination = self.rt
            self.src1 = self.rs
            self.type = "ALU"
        elif self.opcode == 43:
            self.asText = ('SW\t R{0}, {1}(R{2})'.format( self.rt, self.offset, self.rs))
            self.readable = 'SW'
            self.destination = self.rt
            self.src1 = self.rs
            self.type = "MEM"
        elif self.opcode == 35:
            self.asText = ('LW\t R{0}, {1}(R{2})'.format( self.rt, self.offset, self.rs))
            self.readable = 'LW'
            self.destination = self.rt
            self.src1 = self.rs
            self.type = "MEM"
        elif self.opcode == 33:
            self.asText = ('BLTZ\t R{0}, #{1}'.format( self.rs, self.offset << 2))
            self.readable = 'BLTZ'
            self.src1 = self.rs
            self.type = "BRANCH"
        elif self.opcode == 32:
            #Instructions with same opcode

            func = y & 0x0000003F

            if func == 0:
                self.asText = ('SLL\t R{0}, R{1}, #{2}'.format(self.rd, self.rt, self.sa))
                if self.rd == 0 and self.rt == 0 and self.sa == 0:
                    self.asText = 'NOP'
                    self.readable = 'NOP'
            elif func == 34:
                self.asText = ('SUB\t R{0}, R{1}, R{2}'.format(self.rd, self.rs, self.rt))
                self.readable = 'SUB'
                self.destination = self.rd
                self.src1 = self.rs
                self.src2 = self.rt
                self.type = "ALU"
            elif func == 32:
                self.asText = ('ADD\t R{0}, R{1}, R{2}'.format(self.rd, self.rs, self.rt))
                self.readable = 'ADD'
                self.destination = self.rd
                self.src1 = self.rs
                self.src2 = self.rt
                self.type = "ALU"
            elif func == 13:
                self.asText = ('BREAK')
                self.readable = 'BREAK'
            elif func == 8:
                self.asText = 'JR R{0}'.format(self.rs)
                self.readable = 'JR'
                self.src1 = self.rs
            elif func == 2:
                self.asText = ('SRL\t R{0}, R{1}, #{2}'.format(self.rd, self.rt, self.sa))
                self.readable = 'SRL'
                self.destination = self.rd
                self.src1 = self.rt
                self.type = "ALU"
            elif func == 10:
                self.asText = 'MOVZ\t R{0}, R{1}, R{2}'.format(self.rd, self.rs, self.rt)
                self.readable = 'MOVZ'

                self.destination = self.rd
                self.src1 = self.rs
                self.src2 = self.rt
                self.type = "BRANCH"
                
        elif self.opcode == 34:
            self.asText = ('J\t #{0}'.format(self.instru_index << 2))
            self.readable = 'J'

        elif self.opcode == 60:
            self.asText = 'MUL R{0}, R{1}, R{2}'.format(self.rd, self.rs, self.rt)
            self.readable = 'MUL'
            self.destination = self.rd
            self.src1 = self.rs
            self.src2 = self.rt
            self.type = "ALU"
        else:
            #print(str(self.opcode) + " not found")
            self.asText = str(self.opcode) + " not found"
        pass
    def isBreak(self):
        return self.readable == "BREAK"


read_break = False

# read the data and extract the instructions from it
for i in range(0, len(data), 4):
    #print(i)
    x = struct.unpack_from('>i', data, i)[0]
    y = struct.unpack_from('>I', data, i)[0]
    binstr = format(y, '0>32b' ) #format the unsigned int to a binary number

    instruction = Instruction(y, addr)

    if read_break:

        read_break = True

        instruction_as_text[addr] = str(x)
        memory[addr] = str(x)

        output_dis.write(binstr + "\t" + str(addr) + "\t" + str(x) + "\n")

        addr += 4
        continue
    else:
        
        if instruction.isBreak():
            read_break = True
        memory[addr] = instruction

    binstr = binstr[:1] + " " + binstr[1:]
    binstr = binstr[:7] + " " + binstr[7:]
    binstr = binstr[:13] + " " + binstr[13:]
    binstr = binstr[:19] + " " + binstr[19:]
    binstr = binstr[:25] + " " + binstr[25:]
    binstr = binstr[:31] + " " + binstr[31:]

    output_dis.write(binstr + "\t" + str(addr) + "\t" + instruction.asText + "\n")

    addr += 4


def checkXBW(register, entryInPreIssue):
    #check all currently processing instructions to see if destination is the register
    #output.write("\nPRE ISSUE CHECK: there are " + str(preissue.elements) + " elements in preissue")
    #output.write("\nEntryInPreIssue: " + str(entryInPreIssue))
    prei = preissue.checkDestinations(register, entryInPreIssue)
    #output.write("\npreissue check: " + str(prei) + "\n")
    #output.write("\nPRE ALU CHECK:")
    prea = prealu.checkDestinations(register, 2)
    #output.write("\nprea check: " + str(prea) + "\n")
    #output.write("\nPRE MEM CHECK:")
    prem = premem.checkDestinations(register, 2)
    #output.write("\nprem check: " + str(prem) + "\n")
    #output.write("\nPOST ALU CHECK:")
    posta = postalu.checkDestinations(register, 1)
    #output.write("\nposta check: " + str(posta) + "\n")
    #output.write("\nPOST MEM CHECK:")
    postm = postmem.checkDestinations(register, 1)
    #output.write("\npostm check: " + str(postm) + "\n")
    return prei or prea or prem or posta or postm
    
def checkWBR(register):
    return



class WB:
    def __init__(self):
        pass
    def run(self):

        palu = postalu.getData()
        pmem = postmem.getData()

        if not palu == None:
            instruction = palu
            registers[palu.destination] = palu.result
            
            postalu.pop()
        if not pmem == None:
            
            instruction = pmem
            if instruction.opcode == 43:# SW
                memory[instruction.offset + registers[instruction.rs]] = instruction.result
            elif instruction.opcode == 35:# LW
                registers[instruction.destination] = instruction.result
            
            postmem.pop()

class ALU:
    def __int__(self):
        pass
    def run(self):

        ins = prealu.getData()

        if ins == None:
            return

        result = 0

        if ins.opcode == 32:
            #Instructions with the same opcode
            func = ins.y & 0x0000003F

            if func == 0:#SLL
                result = registers[ins.rt] << ins.sa
            elif func == 34:# SUB
                result = str(int(registers[ins.rs]) - int(registers[ins.rt]))
            elif func == 32: # ADD
                result = str(int(registers[ins.rs]) + int(registers[ins.rt]))
            elif func == 2:# SRL
                result = registers[ins.rt] >> ins.sa
        elif ins.opcode == 40:# ADDI
            # if ins.offset >> 15:
            #     ins.offset = twos_comp(ins.offset, 16)
            result = int(registers[ins.rs]) + ins.offset
        elif ins.opcode == 60: # MUL
            result = registers[ins.rs] * registers[ins.rt]

        prealu.pop()
        ins.result = result
        postalu.push(ins)
        


class FETCH:
    def __init__(self):
        self.PC = 96
        self.seenBreak = False
        pass

    def run(self):
        #TODO: branch instruction or cache miss stalls FETCH

        # check if preissue is full or seen break
        if preissue.getElements() > 3 or self.seenBreak:
            return
        # TODO: run branches, jumps, and breaks check for rbw and wbw hazards

        instruction = memory[self.PC]
        if memory[self.PC].valid == 0:
            self.PC += 4
            return
        

        if instruction.readable == "BREAK":
            self.seenBreak = True
            return

        #(J, JR, BEQ, BLTZ
        if instruction.readable == "J" or instruction.readable == "JR" or instruction.readable == "BEQ" or instruction.readable == "BLTZ":
            #branch
            a = 1
            #if all registers are ready perform branch
            #stall until registers are ready

            if checkXBW(instruction.src1, preissue.length):
                #print("stall")
                return
            else:
                #can compute branch
                if instruction.readable == "J":
                    self.PC = instruction.instru_index << 2
                    return
                if instruction.readable == "BLTZ":
                    if (int(registers[instruction.rs]) < 0) == 1:
                        self.PC = (self.PC + (instruction.offset << 2)) + 4


        #     elif func == 8:# JR
        #         jump_to = int(registers[rs])


        # elif opcode == 33: # BLTZ
        #     if (int(registers[rs]) < 0) == 1:
        #         jump_to = (pc + (offset << 2)) + 4
        # elif opcode == 34:
        #     # J
        #     jump_to = instru_index << 2
            
        #     increment_pc = False

        else:
            if memory[self.PC].valid == 1:
                preissue.push(memory[self.PC])

        

        self.PC += 4
        #TODO: branch instruction or cache miss stalls FETCH

        # check if preissue is full or seen break
        if preissue.getElements() > 3 or self.seenBreak:
            return
        # TODO: run branches, jumps, and breaks check for rbw and wbw hazards

        instruction = memory[self.PC]
        if memory[self.PC].valid == 0:
            self.PC += 4
            return
        

        if instruction.readable == "BREAK":
            self.seenBreak = True
            return

        #(J, JR, BEQ, BLTZ
        if instruction.readable == "J" or instruction.readable == "JR" or instruction.readable == "BEQ" or instruction.readable == "BLTZ":
            #branch
            a = 1
            #if all registers are ready perform branch
        else:
            if memory[self.PC].valid == 1:
                preissue.push(memory[self.PC])

        

        self.PC += 4

       

class ISSUE:
    def __init__(self):
        pass
    def run(self):
        issuedThisCycle = 0

        for i in range(0, preissue.length - 1):
            #output.write("\n i = " + str(i))
            instruction = preissue.getData(i)
            if instruction == None:
                continue
            # check if rbw or wbw errors exist on the registers the instruction is trying to use
            #output.write("-------------------------- CHECKING XBW | " + instruction.asText)
            if checkXBW(instruction.destination, i) == False:
                #output.write("\n----------------------NO XBW ERRORS\n")
                if instruction.type == "MEM":
                    if premem.elements < 2:
                        premem.push(instruction)
                        preissue.popEntry(i)
                        issuedThisCycle+=1
                if instruction.type == "ALU":
                    if prealu.elements < 2:
                        prealu.push(instruction)
                        preissue.popEntry(i)
                        issuedThisCycle+=1
                
        
        for i in range(0, preissue.length - 1):
            #output.write("\n i = " + str(i))
            instruction = preissue.getData(i)
            if instruction == None:
                continue
            # check if rbw or wbw errors exist on the registers the instruction is trying to use
            #output.write("-------------------------- CHECKING XBW | " + instruction.asText)
            if checkXBW(instruction.destination, i) == False:
                #output.write("\n----------------------NO XBW ERRORS\n")
                if instruction.type == "MEM":
                    if premem.elements < 2:
                        premem.push(instruction)
                        preissue.popEntry(i)
                        issuedThisCycle+=1
                if instruction.type == "ALU":
                    if prealu.elements < 2:
                        prealu.push(instruction)
                        preissue.popEntry(i)
                        issuedThisCycle+=1
        

class MEM:
    def __init__(self):
        pass
    def run(self):
        
        instruction = premem.getData(0)

        if not instruction == None:

            if instruction.opcode == 43:# SW
                memory[instruction.offset + registers[instruction.rs]] = registers[instruction.rt]

            elif instruction.opcode == 35:# LW
                result = memory[int(instruction.offset) + int(registers[instruction.rs])]
                instruction.result = result
                postmem.push(instruction)
            
            premem.pop()

            

            

        return


def pipeLineEmpty():
    return preissue.elements == 0 and prealu.elements == 0 and premem.elements == 0 and postalu.elements == 0 and postmem.elements == 0

# simulate the instructions
def simulate():
    pc = 96
    cycle = 1


    fetch = FETCH()
    issue = ISSUE()
    alu = ALU()
    wb = WB()
    mem = MEM()

    
    code_finished = False

    while True:

        wb.run()
        mem.run()
        alu.run()
        issue.run()
        fetch.run()

        # display the current cycle of the simulation
        output.write("--------------------\n")
        output.write(("Cycle:\t" + str(cycle) + "\n\n"))
        output.write("Pre-Issue Buffer:\n")
        preissue.writeDataToFile(output)
        output.write("Pre_ALU Queue:\n")
        prealu.writeDataToFile(output)
        output.write("Post_ALU Queue:\n")
        postalu.writeDataToFile(output)
        output.write("Pre_MEM Queue:\n")
        premem.writeDataToFile(output)
        output.write("Post_MEM Queue:\n")
        postmem.writeDataToFile(output)
        output.write("\nRegisters\n")
        output.write("R00:\t" + "\t".join(map(str,registers[0:8])) + "\n")
        output.write("R08:\t" + "\t".join(map(str,registers[8:16])) + "\n")
        output.write("R16:\t" + "\t".join(map(str,registers[16:24])) + "\n")
        output.write("R24:\t" + "\t".join(map(str,registers[24:32])) + "\n")
        output.write("\nData\n")

        #test1

        if "t1.bin" in sys.argv[1]:
            output.write("128:\t" + str(memory[128]) + "\t" + str(memory[132]) + "\n\n")

        #test2
        if "t2.bin" in sys.argv[1]:
            s = "128:"
            for i in range(0,8):
                s = s + "\t" + str(memory[128 + i * 4])
            s = s + "\n"
            output.write(s)
            s = "160:"
            for i in range(0,8):
                s = s + "\t" + str(memory[160 + i * 4])
            s = s + "\n"
            output.write(s)
            s = "128:"
            for i in range(0,2):
                s = s + "\t" + str(memory[192 + i * 4])
            s = s + "\n"
            output.write(s)

        #test3
        if "t3.bin" in sys.argv[1]:
            s = "136:"
            for i in range(0,6):
                s = s + "\t" + str(memory[136 + i * 4])
            s = s + "\n"
            output.write(s)

        if "t4.bin" in sys.argv[1]:
            s = "144:"
            for i in range(0,2):
                s = s + "\t" + str(memory[144 + i * 4])
            s = s + "\n"
            output.write(s)







        if fetch.seenBreak and pipeLineEmpty():
            break

        cycle += 1


        

simulate()
output.close()