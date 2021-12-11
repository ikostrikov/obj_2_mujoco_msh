import os
import struct
import sys

if __name__ == "__main__":
    obj_f_name = sys.argv[1]
    assert obj_f_name[-4:] == ".obj"

    current_material = None
    faces_by_material = {}

    mtl = open(obj_f_name[:-4] + '.mtl', 'r')
    materials = {} 
    current_material = None
    for line in mtl:
        arr = line.strip().split(' ')
        if arr[0] == 'newmtl':
            current_material = arr[1]
            materials[current_material] = {
                "name": current_material
            }
        elif arr[0] == 'Kd':
            materials[current_material]["rgba"] = (' '.join([str(x) for x in arr[1:] + [1]]))
        elif arr[0] == 'Ka':
            pass
        elif arr[0] == 'Ks':
            materials[current_material]["specular"] = str(arr[1])
        elif arr[0] == 'Ke':
            materials[current_material]["emission"] = str(arr[1])
        elif arr[0] == 'map_Kd':
            materials[current_material]["texture"] = arr[1]
        else:
            print(arr)

    xml = open(obj_f_name[:-4] + '_misc.xml', 'w')
    for _, material in materials.items():
        xml_str = "<material "
        for k, v in material.items():
            xml_str += f"{k}=\"{v}\" "
        xml_str += "/>\n"
        xml.write(xml_str)
        xml.flush()

    v = []
    vt = []
    vn = []
    obj = open(obj_f_name, 'r')
    for line in obj:
        arr = line.split()
        if len(arr) == 0:
            continue
        
        if arr[0] == 'usemtl':
            current_material = arr[1]
        elif arr[0] == 'v':
            assert len(arr) == 4
            v.append([float(arr[i]) for i in range(1, 4)])
        elif arr[0] == 'vt':
            assert len(arr) == 4 or len(arr) == 3
            vt.append([float(arr[i]) for i in range(1, 3)])
        elif arr[0] == 'vn':
            assert len(arr) == 4
            vn.append([float(arr[i]) for i in range(1, 4)])
        elif arr[0] == 'f':
            if current_material not in faces_by_material:
                faces_by_material[current_material] = []
            faces_by_material[current_material].append([arr[i].split("/") for i in range(1, len(arr))])
        else:
            print(arr)

    for material, faces in faces_by_material.items():
        output_v = []
        output_vn = []
        output_vt = []
        output_f = []
        msh_f_name = obj_f_name[:-4] + f"_{material}.msh"

        for i in faces:
            assert len(i) == 3
            for j in i:
                v_idx = int(j[0]) - 1
                output_v.append(v[v_idx])
                try:
                    vt_idx = int(j[1]) - 1
                    output_vt.append(vt[vt_idx])
                except:
                    output_vt.append([0.0, 0.0])
                try:
                    vn_idx = int(j[2]) - 1
                    output_vn.append(vn[vn_idx])
                except:
                    output_vn.append([0.0, 0.0, 0.0])
            output_f.append(
                [len(output_v) - 3,
                len(output_v) - 2,
                len(output_v) - 1])

        print("len(v)=", len(output_v))
        print("len(vn)=", len(output_vn))
        print("len(vt)=", len(output_vt))
        print("len(f)=", len(output_f))
        out = open(msh_f_name, 'wb')

        integer_packing = "=i"
        float_packing = "=f"

        def int_to_bytes(input):
            assert type(input) == int
            return struct.pack(integer_packing, input)

        def float_to_bytes(input):
            assert type(input) == float
            return struct.pack(float_packing, input)

        out.write(int_to_bytes(len(output_v)))
        out.write(int_to_bytes(len(output_vn)))
        out.write(int_to_bytes(len(output_vt)))
        out.write(int_to_bytes(len(output_f)))

        for i in output_v:
            for j in range(3):
                out.write(float_to_bytes(i[j]))
        for i in output_vn:
            for j in range(3):
                out.write(float_to_bytes(i[j]))
        for i in output_vt:
            out.write(float_to_bytes(i[0]))
            out.write(float_to_bytes(1 - i[1]))
        for i in output_f:
            for j in range(3):
                out.write(int_to_bytes(i[j]))
        out.close()

        geom_name = msh_f_name.split('/')[-1]
        xml.write(f"<mesh name=\"{material}\" file=\"{geom_name}\"/>\n")
        print("actual file size=", os.path.getsize(msh_f_name))

        expected_file_size = 16 + 12 * (len(output_v) + len(output_vn) +
                                        len(output_f)) + 8 * len(output_vt)
        print("expected_file_size=", expected_file_size)

    for material in faces_by_material.keys():
        xml.write(f"<geom type=\"mesh\" mesh=\"{material}\" material=\"{material}\" />\n")
