from Crypto.Hash import SHA256
from graphviz import Digraph
from random import randint
import copy
import math
import time

from graphviz.dot import node


class TreeNode:
    '''
    树节点类
    '''

    def __init__(self, value, leftNode=None, rightNode=None, hash=None, childNum=None, depth=None, id=None, father=None, primeNum=None, hashIsRight=True, generation=None,):
        self.value = value              # 节点保存的数据
        self.leftNode = leftNode        # 节点的左孩子
        self.rightNode = rightNode      # 节点的右孩子
        self.hash = hash                # hash值
        self.childNum = childNum        # 节点拥有的孩子数量
        self.depth = depth              # 节点的高度
        self.id = id                    # 唯一的标号
        self.father = father            # 父亲节点
        self.primeNum = primeNum        # 大素数
        self.hashIsRight = hashIsRight  # 该节点的hash值是否正确
        self.generation = generation    # 该节点的添加代
        # self.rm = rm

    def __str__(self):
        # 可以打印树中某个节点的信息
        return 'Node(value='+self.value+', prime='+self.primeNum+', hash='+self.hash+')'


class MerkleTree:
    '''
    Merkle 树用于保证数据的完整性
    一、查询某一个元素是否《存在》树上
    二、查询某一个元素是否《不在》树上
    '''

    def __init__(self):
        self.history = 1  # 创建节点的代数，初始化为第一代节点
        self.newNodes = []
        self.root = TreeNode(
            value='root',
            hash='',
            childNum=0,
            depth=0,
            id=str(time.time()),
            generation=self.history,
            primeNum=self.generate_prime_number()
        )

    def calculate_hash(self, data):
        '''
        函数功能：计算hash值（SHA256）
        '''
        bytes_data = bytearray(data, "utf-8")
        h = SHA256.new()
        h.update(bytes_data)
        return str(h.hexdigest())

    def miller_rabin(self, p):
        '''
        函数功能：miller rabin 素性检验是一种素数判定法则，利用随机化算法判断一个数是合数还是可能是素数。
        '''
        if p == 1:
            return False
        if p == 2:
            return True
        if p % 2 == 0:
            return False
        m, k, = p - 1, 0
        while m % 2 == 0:
            m, k = m // 2, k + 1
        a = randint(2, p - 1)
        x = pow(a, m, p)
        if x == 1 or x == p - 1:
            return True
        while k > 1:
            x = pow(x, 2, p)
            if x == 1:
                return False
            if x == p - 1:
                return True
            k = k - 1
        return False

    def is_prime(self, p, r=40):
        '''
        函数功能：判断是否是素数
        '''
        for _ in range(r):
            if self.miller_rabin(p) == False:
                return False
        return True

    def generate_prime_number(self, index=10):
        '''
        函数功能：生成一个素数
        '''
        num = 0
        for _ in range(index):
            num = num * 2 + randint(0, 1)
        while self.is_prime(num) == False:
            num = num + 1
        return str(num)

    def bulid_complete_binary_tree(self, treeNodeData):
        '''
        功能：构造一颗完全二叉树
        '''
        # 如果给定构造的节点数据为空，返回 Merkle 树初始状态
        if len(treeNodeData) == 0:
            return self.root

        # 计算能构造一颗完全二叉树所需要的节点数量
        treeDepth = math.ceil(math.log2(len(treeNodeData)))

        # 为整棵树补充需要的节点（将最后一个节点复制若干次）
        for _ in range(2**treeDepth - len(treeNodeData)):
            copyNodeString = treeNodeData[len(treeNodeData)-1].value
            copyNodeHash = treeNodeData[len(treeNodeData)-1].hash
            copyNode = TreeNode(
                value=copyNodeString,
                hash=self.calculate_hash(copyNodeHash),
                depth=0,
                childNum=0,
                id=str(time.time()),
                primeNum=self.generate_prime_number(),
                generation=self.history,
            )
            treeNodeData.append(copyNode)

        # 构造所有的中间节点 -> nodeQueue
        nodeQueue = []
        for index in range(0, len(treeNodeData), 2):
            mergeStrings = treeNodeData[index].value + \
                ' '+treeNodeData[index+1].value
            hashString = self.calculate_hash(
                treeNodeData[index].hash+treeNodeData[index+1].hash)
            mergeNode = TreeNode(
                value=mergeStrings,
                hash=hashString,
                leftNode=treeNodeData[index],
                rightNode=treeNodeData[index+1],
                depth=1,
                childNum=2,
                id=str(time.time()),
                primeNum=str(
                    int(treeNodeData[index].primeNum)*int(treeNodeData[index+1].primeNum)),
                generation=self.history,
            )
            treeNodeData[index].father = mergeNode
            treeNodeData[index+1].father = mergeNode
            nodeQueue.append(mergeNode)

        # 逐层向上合并节点
        while len(nodeQueue) > 1:
            temp = []
            for index in range(0, len(nodeQueue), 2):
                mergeStrings = nodeQueue[index].value + \
                    ' '+nodeQueue[index+1].value
                hashString = self.calculate_hash(
                    nodeQueue[index].hash+nodeQueue[index+1].hash)
                mergeNode = TreeNode(
                    value=mergeStrings,
                    hash=hashString,
                    depth=nodeQueue[index].depth+1,
                    childNum=nodeQueue[index].childNum +
                    nodeQueue[index+1].childNum,
                    leftNode=nodeQueue[index],
                    rightNode=nodeQueue[index+1],
                    id=str(time.time()),
                    primeNum=str(
                        int(nodeQueue[index].primeNum)*int(nodeQueue[index+1].primeNum)),
                    generation=self.history,
                )
                nodeQueue[index].father = mergeNode
                nodeQueue[index+1].father = mergeNode
                temp.append(mergeNode)

            # 一棵完全2叉树构建完成
            nodeQueue = temp
        return nodeQueue[0]

    def build_merkle_tree(self, nodeData, way='filling', sorted=False):
        if len(nodeData) == 0:
            print('INFO: 构建了个寂寞')
            return

        # 将每一个节点数据构造节点
        if sorted == True:
            nodeData = [int(i) for i in nodeData]
            nodeData.sort()
            nodeData = [str(i) for i in nodeData]

        rootPrime = 1
        # 构造每一个叶子节点
        treeNodeData = []
        for data in nodeData:
            while True:
                newNodePrime = self.generate_prime_number()
                if int(rootPrime) == 1:
                    break
                if int(rootPrime) % int(newNodePrime) == 0 and int(rootPrime) > int(newNodePrime):
                    # print(newNodePrime, ' 重复！！')
                    continue
                else:
                    break
            rootPrime = str(int(rootPrime) * int(newNodePrime))
            thisTime = str(time.time())
            newNode = TreeNode(
                value=data,
                hash=self.calculate_hash(data+newNodePrime+thisTime),
                depth=0,
                childNum=0,
                id=thisTime,
                primeNum=newNodePrime,
                generation=self.history,
            )
            treeNodeData.append(newNode)
            print('INFO: 节点构造完成：', str(newNode))

        if way == 'filling':
            self.root = self.bulid_complete_binary_tree(treeNodeData)
            self.newNodes = [self.root]

        elif way == 'imbalance':
            # 计算能构造一颗完全二叉树的节点数量
            treeDepth = int(math.log2(len(treeNodeData)))  # 向下取整

            if treeDepth == 0:
                offset = 0
            else:
                offset = 2**treeDepth

            # 分叉两个 子集
            # 子集1：可以构造一棵完全二叉树
            # 子集2：不足一颗完全二叉树
            treeNodeDataSub_1 = [treeNodeData[i] for i in range(0, offset)]
            treeNodeDataSub_2 = [treeNodeData[i]
                                 for i in range(offset, len(treeNodeData))]

            # print(len(treeNodeDataSub_1))
            # print(len(treeNodeDataSub_2))

            self.root = self.bulid_complete_binary_tree(treeNodeDataSub_1)
            # 将剩余的不足2的整数幂的节点，依次插入
            for node in treeNodeDataSub_2:
                self.insert(node, addAgain=True)

    def add(self, Data):
        self.history += 1
        rootPrime = self.root.primeNum
        # 构造每一个叶子节点
        treeNodeData = []
        while True:
            newNodePrime = self.generate_prime_number()
            if int(rootPrime) == 1:
                break
            if int(rootPrime) % int(newNodePrime) == 0 and int(rootPrime) > int(newNodePrime):
                # print(newNodePrime, ' 重复！！')
                continue
            else:
                break
        rootPrime = str(int(rootPrime) * int(newNodePrime))
        thisTime = str(time.time())
        newNode = TreeNode(
            value=Data,
            hash=self.calculate_hash(Data+newNodePrime+thisTime),
            depth=0,
            childNum=0,
            id=thisTime,
            primeNum=newNodePrime,
            generation=self.history,
        )
        treeNodeData.append(newNode)
        for node in treeNodeData:
            self.insert(node)

        print('INFO: 节点构造完成：', str(newNode))

    def insert(self, node, addAgain=False):
        if addAgain == False:
            self.newNodes = []
        self.newNodes.append(node)
        canNodes = []
        searchQueue = []
        thisNode = self.root
        if 2**(thisNode.depth) != thisNode.childNum:
            # 说明这个节点是不够的
            searchQueue.append(self.root)
            while len(searchQueue) != 0:
                thisNode = searchQueue[0]
                searchQueue.pop(0)
                # print(str(thisNode))
                if thisNode.leftNode == None or thisNode.rightNode == None and thisNode.depth != 0:
                    # print('check', str(thisNode))
                    canNodes.append(thisNode)

                if thisNode.rightNode and thisNode.rightNode.depth != 0 and 2**thisNode.rightNode.depth != thisNode.rightNode.childNum:
                    searchQueue.append(thisNode.rightNode)
                if thisNode.leftNode and thisNode.leftNode.depth != 0 and 2**thisNode.leftNode.depth != thisNode.leftNode.childNum:
                    searchQueue.append(thisNode.leftNode)

                # print('满足条件的孩子',[i.depth for i in searchQueue])
            thisNode = canNodes[len(canNodes)-1]
        # print('##################')
        # print(str(thisNode))
        # print('##################')
        if thisNode == self.root:
            #######################################
            # 原先的树已经满了，需要构建新的根，和右分支 #
            # 分两种情况：                          #
            # 一、原先的树不是“满”，而是完全没有       #
            # 二、第一步完成之后完全缺失右子树         #
            # 二、满树                             #
            #######################################

            if thisNode.value == 'root':
                # 第一种情况 原先的树不是“满”，而是完全没有
                # 构造新树根
                newRoot = TreeNode(
                    value=node.value,
                    hash=self.calculate_hash(node.hash),
                    depth=node.depth+1,
                    childNum=node.childNum+1,
                    leftNode=node,
                    rightNode=None,
                    id=str(time.time()),
                    primeNum=str(int(node.primeNum)),
                    generation=self.history,
                )
                node.father = newRoot
                self.root = newRoot  # 移植成功
                # 记录新加入的节点
                self.newNodes.append(newRoot)
                return

            elif thisNode.depth == 1 and thisNode.rightNode == None:
                # 第二种情况 第一步完成之后完全缺失右子树
                thisNode.value = thisNode.value+' '+node.value
                thisNode.hash = self.calculate_hash(
                    thisNode.leftNode.hash+node.hash)
                thisNode.childNum += 1
                thisNode.primeNum = str(
                    int(thisNode.primeNum)*int(node.primeNum))

                thisNode.rightNode = node
                node.father = thisNode
                return

            # 第三  种情况 满树
            nowTreeDepth = thisNode.depth
            newright = node
            for _ in range(nowTreeDepth):
                newright_temp = TreeNode(
                    value=node.value,
                    hash=self.calculate_hash(newright.hash),
                    depth=newright.depth+1,
                    leftNode=newright,
                    childNum=1,
                    id=str(time.time()),
                    primeNum=newright.primeNum,
                    generation=self.history,
                )
                self.newNodes.append(newright_temp)
                newright.father = newright_temp
                newright = newright_temp
            # 循环结束 构建右分支完成，并进行添加

            # 构造新树根
            newRoot = TreeNode(
                value=thisNode.value+' '+newright.value,
                hash=self.calculate_hash(thisNode.hash+newright.hash),
                depth=thisNode.depth+1,
                childNum=thisNode.childNum+newright.childNum,
                leftNode=thisNode,
                rightNode=newright,
                id=str(time.time()),
                primeNum=str(int(thisNode.primeNum)*int(newright.primeNum)),
                generation=self.history,
            )
            self.newNodes.append(newRoot)
            thisNode.father = newRoot
            newright.father = newRoot
            self.root = newRoot  # 移植成功

        else:
            #######################################
            # 在右分支上进行添加节点，补充整棵树        #
            # 分两种情况：                          #
            # 1. 在左叶子节点的旁边直接添加右叶子节点   #
            # 2. 添加右边的分支，然后作为其左叶子节点添加#
            #######################################

            # 第一种情况 直接添加
            if thisNode != None and thisNode.depth == 1:
                if thisNode.leftNode == None:
                    thisNode.leftNode = node
                else:
                    thisNode.rightNode = node
                node.father = thisNode

            # 第二种情况 先构建右分支（左延伸）
            if thisNode != None and thisNode.depth != 1:

                if thisNode.rightNode == None:
                    nowTreeDepth = thisNode.leftNode.depth
                else:
                    nowTreeDepth = thisNode.rightNode.depth

                newright = node
                for _ in range(nowTreeDepth):
                    newright_temp = TreeNode(
                        value=node.value,
                        hash=self.calculate_hash(newright.hash),
                        depth=newright.depth+1,
                        leftNode=newright,
                        childNum=1,
                        id=str(time.time()),
                        primeNum=newright.primeNum,
                        generation=self.history,
                    )
                    self.newNodes.append(newright_temp)
                    newright.father = newright_temp
                    newright = newright_temp
                # 循环结束 构建右分支完成，并进行添加

                if thisNode.rightNode == None:
                    thisNode.rightNode = newright
                else:
                    thisNode.leftNode = newright

                newright.father = thisNode

            while thisNode != None:
                MergeString = ''
                MergeHash = ''
                MergePrime = 1
                if thisNode.leftNode != None:
                    MergeString = thisNode.leftNode.value
                    MergeHash = thisNode.leftNode.hash
                    MergePrime = int(thisNode.leftNode.primeNum)
                if thisNode.rightNode != None:
                    MergeString = MergeString + ' ' + thisNode.rightNode.value
                    MergeHash = MergeHash + thisNode.rightNode.hash
                    MergePrime = MergePrime * int(thisNode.rightNode.primeNum)

                thisNode.value = MergeString
                thisNode.hash = self.calculate_hash(MergeHash)
                thisNode.childNum += 1
                thisNode.primeNum = str(MergePrime)
                thisNode = thisNode.father

    def merkle_path(self, proofPath):
        '''
        描述：从叶子到树根的路径称为 Merkle Path ，它可以用来证明事务(string)的存在
        参数：proofPath 已经构建好的证明路径
        '''
        if proofPath == None:
            print('INFO: 请检查验证路径的合理性')
            return
        queue = [proofPath]
        thisNode = None
        while len(queue) != 0:
            thisNode = queue[0]
            queue.pop(0)
            if thisNode.leftNode:
                queue.append(thisNode.leftNode)
            if thisNode.rightNode:
                queue.append(thisNode.rightNode)

        thisNode = thisNode.father
        while thisNode != None:
            mergeHash = ''
            if thisNode.leftNode:
                mergeHash = thisNode.leftNode.hash
            if thisNode.rightNode:
                mergeHash = mergeHash + thisNode.rightNode.hash

            mergeHash = self.calculate_hash(mergeHash)
            if thisNode.hash == mergeHash:
                thisNode.hashIsRight = True
            else:
                # print('error')
                thisNode.hashIsRight = False

            thisNode.hash = mergeHash
            thisNode = thisNode.father

        dot = self.show(proofPath, proof=True)
        if proofPath.hashIsRight:
            dot.attr(label=r'\nMerkle tree is complete')
        else:
            dot.attr(label=r'\nMerkle tree has been modified')
        return dot

    def search(self, prime, showNode=False):
        # 保证数据类型正确
        prime = int(prime)

        # 复制这棵树
        proofNode = copy.deepcopy(self.root)
        proofPath = proofNode

        thisNode = self.root
        if int(thisNode.primeNum) % prime == 0:

            # 如果是 叶子节点 就退出循环
            while thisNode.leftNode or thisNode.rightNode:

                if thisNode.leftNode and int(thisNode.leftNode.primeNum) % int(prime) == 0:
                    thisNode = thisNode.leftNode

                    if proofNode.rightNode:
                        proofNode.rightNode.leftNode = None
                        proofNode.rightNode.rightNode = None
                        proofNode.rightNode.value = 'Ref Hash'
                    proofNode.value = '✱'
                    proofNode = proofNode.leftNode

                elif thisNode.rightNode and int(thisNode.rightNode.primeNum) % int(prime) == 0:
                    thisNode = thisNode.rightNode

                    if proofNode.leftNode:
                        proofNode.leftNode.leftNode = None
                        proofNode.leftNode.rightNode = None
                        proofNode.leftNode.value = 'Ref Hash'
                    proofNode.value = '✱'
                    proofNode = proofNode.rightNode
                else:
                    break
            proofNode.value = 'Target'
            proofPath.value = 'Root'

        else:
            thisNode = None
            proofPath = None
            print('INFO: 这棵树上没有这个叶子')

        return thisNode, proofPath

    def tampering_test(self, proofPath, Index):
        if proofPath == None:
            print('INFO: 请检查验证路径的合理性')
            return

        proofPath = copy.deepcopy(proofPath)
        queue = [proofPath]
        count = 0
        thisNode = None
        while len(queue) != 0:
            thisNode = queue[0]
            queue.pop(0)
            if not(thisNode.leftNode or thisNode.rightNode):
                count += 1
            if count == Index:
                thisNode.value = 'Modified'
                thisNode.hash = 'chaos'
                break
            if thisNode.leftNode:
                queue.append(thisNode.leftNode)
            if thisNode.rightNode:
                queue.append(thisNode.rightNode)
        return proofPath

    def getTreePrime(self,):
        allPrime = []
        queue = [self.root]
        thisNode = None
        while len(queue) != 0:
            thisNode = queue[0]
            queue.pop(0)
            if thisNode.leftNode == None and thisNode.rightNode == None:
                allPrime.append(thisNode.primeNum)
            if thisNode.leftNode:
                queue.append(thisNode.leftNode)
            if thisNode.rightNode:
                queue.append(thisNode.rightNode)
        return allPrime

    def compare(self, showHistory=False):
        dot = self.show()
        if showHistory == False:
            for node in self.newNodes:
                dot.node(node.id, _attributes={'fillcolor': '#FFCDD2'})
        else:
            allColor = ['#FFCDD2', '#FFE0B2', '#FFF9C4',
                        '#C8E6C9', '#B2EBF2', '#BBDEFB', '#E1BEE7']
            queue = [self.root]
            thisNode = None
            while len(queue) != 0:
                thisNode = queue[0]
                queue.pop(0)
                dot.node(thisNode.id, _attributes={
                    'fillcolor': allColor[abs(thisNode.generation-self.history) % len(allColor)]
                }
                )
                if thisNode.leftNode:
                    queue.append(thisNode.leftNode)
                if thisNode.rightNode:
                    queue.append(thisNode.rightNode)
        return dot


    def show(self, node=0, proof=False, showDepth=True, showMinDepth=False, string=None):
        # 默认值为展示整棵树
        if node == 0:
            node = self.root

        # 如果输入不合法，直接返回
        if node == None:
            return

        # 构建可视化的对象
        dot = Digraph(name='MerkleTree', format='png')

        # 展示树的高度
        if showDepth:
            # 标注树的高度
            for i in range(node.depth+1):
                dot.node(
                    name=str(i),
                    label='depth : '+str(node.depth-i),
                    _attributes={'color': '#FFFFFF'})

            for i in range(node.depth):
                dot.edge(str(i), str(i+1), _attributes={'arrowhead': 'none', 'color': '#FFFFFF'})

        # 使用层次遍历
        queue = [node]
        countofProof = 0  # 标志用于作证hash的节点序号

        while len(queue) != 0:
            # temp 变量用于存储 某一层（depth=i）的所有节点信息
            temp = []

            for node_i in queue:
                # 现将节点所包含的树叶的个数加进去
                nodeString = 'childs: ' + str(node_i.childNum)

                # 如果节点的 value 太长，这样不利于显示，所以 “掐头去尾” 的显示
                if len(node_i.value) > 8:
                    strings = str(node_i.value).split(' ')
                    strsL = len(strings)-1
                    nodeString = strings[0] + ' ~ ' + \
                        strings[strsL] + '\n' + nodeString
                else:
                    nodeString = node_i.value + '\n' + nodeString

                # 可视化节点的默认颜色
                node_color = '#FFFFFF'

                # 如果是 “证明Merkle路径” 时候用到的，可以为该事务染上直观的颜色
                if proof == True:
                    if node_i.value == 'Ref Hash':
                        # 用于佐证的节点 橙色
                        node_color = '#FFA500'
                        nodeString = node_i.value

                    elif node_i.value == 'Target':
                        # “请求者” 需要证明的节点 蓝色
                        node_color = '#BBDEFB'
                        nodeString = node_i.value

                    elif node_i.value == 'Modified':
                        # 被篡改的节点 灰色
                        node_color = '#E0E0E0'
                        nodeString = node_i.value

                    elif node_i.value == '✱':
                        # 如果为中间连接的节点
                        # 如果节点的hash值计算的结果 不一致 红色
                        if node_i.hashIsRight == False:
                            node_color = '#FFCDD2'
                            nodeString = '✕'
                        else:
                            # 否则 绿色
                            node_color = '#C8E6C9'
                            nodeString = '✓'

                    elif node_i.value == 'Root':
                        # 根节点
                        if node_i.hashIsRight == False:
                            node_color = '#FFCDD2'
                            nodeString = 'Root ✕'
                        else:
                            # 否则 绿色
                            node_color = '#C8E6C9'
                            nodeString = 'Root ✓'

                    # 叶子节点，为叶子节点标注序号
                    if not(node_i.leftNode or node_i.rightNode):
                        countofProof += 1
                        nodeString = str(countofProof)+'\n'+nodeString

                if showMinDepth == True:
                    nodeString += '\n minD: '+str(node_i.rm)
                # 可视化对象中添加节点
                # 设置好上面设置好的相关属性
                dot.node(
                    name=node_i.id,
                    label=nodeString,
                    style='filled',
                    fillcolor=node_color)

                # 构建与左叶子节点的连接关系
                if node_i.leftNode:
                    temp.append(node_i.leftNode)
                    dot.edge(node_i.id, node_i.leftNode.id)

                # 构建与右叶子节点的连接关系
                if node_i.rightNode:
                    temp.append(node_i.rightNode)
                    dot.edge(node_i.id, node_i.rightNode.id)

            # 跳转到下一层
            queue = temp

            if string:
                dot.attr(label=r'\n'+string)
                
        return dot
