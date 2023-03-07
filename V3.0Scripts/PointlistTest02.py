import os
import re
import glob
import shutil
from FrameAnalyseUtil import *


if __name__ == "__main__":
    # TODO 新增指定输出目录，这样融合脚本的输出和分割脚本的输入就可以作为最终的mod文件夹了。
    #  用1.0脚本分析原神dump文件，和原神的脚本做对比，拆解分析原神脚本思路
    #  新增一个方法：pointlist和trianglelist配对后只输出配对成功的
    #  新增方法，分析dump foulder中所有的pointlist的vertex count，并从trianglelist中找出对应的，然后全部转换并输出

    # TODO 必须参考原神的脚本，不然有些无法对应的无法导入

    # Here is the ROOT VS the game currently use, Naraka use e8425f64cfb887cd as it's ROOT VS now.
    # and this value is different between games which use pointlist topology.
    NarakaRootVS = "e8425f64cfb887cd"

    # Here is your Loader location.
    NarakaLoaderFolder = "C:/Users/Administrator/Desktop/GenshinLoader/"

    # Set work dir, here is your FrameAnalysis dump dir.
    NarakaFrameAnalyseFolder = "FrameAnalysis-2023-03-06-135256"

    os.chdir(NarakaLoaderFolder + NarakaFrameAnalyseFolder + "/")
    if not os.path.exists('output'):
        os.mkdir('output')

    print("----------------------------------------------------------------------------------")
    print("开始读取所有pointlist和trianglelist的index：")
    pointlist_indices_dict, trianglelist_indices_dict = get_all_pointlist_trianglelist_index()
    # print(pointlist_indices_dict)
    """
    此处输出格式为：
    {'000001': b'1126', '000002': b'523'}
    key为索引，value为vb文件的vertex-count
    """

    print("----------------------------------------------------------------------------------")
    print("移动所有ib文件到output目录")
    for index in pointlist_indices_dict:
        filename = glob.glob(str(index)+'-ib*.txt')[0]
        print("Moving ： " + filename + " ....")
        shutil.copy2(filename, 'output/' + filename)

    print("----------------------------------------------------------------------------------")
    print("读取pointlist的index列表中所有vb0的POSITION、NORMAL、TANGENT信息")
    for index in pointlist_indices_dict:
        retain_element_list = [b"POSITION", b"NORMAL", b"TANGENT"]
        print("读取对应的vb0的element_list信息")
        # 读取headerinfo
        header_info = get_header_info_by_elementnames(retain_element_list)

        # Set vertex count
        header_info.vertex_count = pointlist_indices_dict.get(index)

        # 设置topology为trianglelist，因为pointlist里面的默认是pointlist无法被读取
        header_info.topology = b"trianglelist"

        # Solve TEXCOORD1 can't match the element's semantic name TEXCOORD problem.
        # 给element_list设置正确的索引偏移量
        element_aligned_byte_offsets = {}
        new_element_list = []
        for element in header_info.elementlist:
            # print("-----------------")
            # print(element.semantic_name)
            # print(element.semantic_index)
            element_aligned_byte_offsets[element.semantic_name] = element.aligned_byte_offset
            new_element_list.append(element)
        header_info.elementlist = new_element_list

        # 输出elementlist看一下
        for element in new_element_list:
            print(element.semantic_name)
            print(element.aligned_byte_offset)
        print("-----------------------------")

        # 读取vb0文件的vertex_data
        vb0_vertex_data = read_vb_files_vertex_data(index, only_vb0=True).get(b"vb0")
        # print(output)
        # print(output.__len__()) 只读取vb0的话，这里应该为1
        """
        这里的输出格式为：
        {
        b'vb0': {b'0': [<DataStructure.VertexData object at 0x000002287F9950D0>  , <DataStructure.VertexData object at 0x000002287F9C4390>], 
                b'1': [<DataStructure.VertexData object at 0x000002287F9C43D0>, <DataStructure.VertexData object at 0x000002287F9C45D0>]
                .....},
        b'vb1': {b'0': [<DataStructure.VertexData object at 0x000002287F9950D0>  , <DataStructure.VertexData object at 0x000002287F9C4390>], 
                b'1': [<DataStructure.VertexData object at 0x000002287F9C43D0>, <DataStructure.VertexData object at 0x000002287F9C45D0>]
                .....}
        }
        """
        print("保留指定的元素列表：")
        new_vb0_vertex_data = {}
        for offset in vb0_vertex_data:
            vertex_data_list = vb0_vertex_data.get(offset)
            new_vertex_data_list = []
            for vertex_data in vertex_data_list:
                """
                class VertexData:
                    vb_file_number = b"vb0"  # vb0
                    index = None
                    aligned_byte_offset = None
                    element_name = None
                    data = None
                """
                element_name = vertex_data.element_name
                if element_name in retain_element_list:
                    # print("重新设置vertex-data 中对应的alygned_byte_offset")
                    vertex_data.aligned_byte_offset = element_aligned_byte_offsets.get(element_name)

                    new_vertex_data_list.append(vertex_data)
            new_vb0_vertex_data[offset] = new_vertex_data_list
        print(new_vb0_vertex_data.get(b"0"))

        print("输出vb0文件")
        output_vb_fileinfo = VbFileInfo()
        """
        class VbFileInfo:
            header_info = HeaderInfo()
            vb0_vertex_data = {}
            output_filename = None
        """
        output_vb_fileinfo.header_info = header_info
        output_vb_fileinfo.vb0_vertex_data = new_vb0_vertex_data
        output_vb_fileinfo.output_filename = "output/"+ glob.glob(str(index) + '-vb0*txt')[0]

        # Write to vb file.
        output_model_txt(output_vb_fileinfo)



